use crate::ClamResponse;
use crate::error::ApiError;
use crate::state::ServiceState;
use axum::extract::{Path, Request};
use axum::extract::{Query, State};
use axum::http::{StatusCode, header};
use axum::middleware::Next;
use axum::response::Response;
use axum::response::{IntoResponse, Redirect};
use axum_extra::extract::cookie::{Cookie, CookieJar};
use base64::{Engine as _, engine::general_purpose::STANDARD};
use derive_getters::Getters;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::sync::Arc;
use std::time::{SystemTime, UNIX_EPOCH};
use uuid::Uuid;

use tracing::{debug, error, warn};

use jsonwebtoken;

/// OpenID Provider Metadata.
#[derive(Debug, Deserialize)]
pub struct OpenIdConfiguration {
    //standard fields
    pub issuer: String,
    pub authorization_endpoint: String,
    pub token_endpoint: String,
    pub jwks_uri: String,
    pub response_types_supported: Vec<String>,
    pub subject_types_supported: Vec<String>,
    pub id_token_signing_alg_values_supported: Vec<String>,

    // Optional standard fields
    pub userinfo_endpoint: Option<String>,
    pub end_session_endpoint: Option<String>,
    pub scopes_supported: Option<Vec<String>>,
    pub token_endpoint_auth_methods_supported: Option<Vec<String>>,
}

#[derive(Deserialize)]
/// Auth code as passed from the OIDC IdP to our callback endpoint after succesful login
pub struct AuthRequest {
    code: String,
    state: isize,
}

#[derive(Debug, Deserialize)]
struct OidcClaims {
    // The standard OIDC claim for user emails
    email: Option<String>,

    // Issuer identifier: the OIDC provider that issued this ID token, this is URL, we don't really use this because we only have one configured anyway
    #[allow(dead_code)]
    iss: String,

    // Subject identifier: a stable, provider-specific ID for the authenticated user.
    sub: String,

    /// Whether the provider says the email address has been verified.
    email_verified: Option<bool>,
}

#[derive(Serialize, Deserialize)]
pub struct TokenResponse {
    access_token: String,
    id_token: Option<String>,
    token_type: String,
    expires_in: i64,
}

#[derive(Clone, Getters)]
pub struct OidcSession {
    username: String,

    // whilst we could store the access token here, we don't really have any need for it after the user has logged in,
    // we're not calling any other APIs on the user's behalf nor requesting more data from the UserInfo endpoint.
    // so we don't keep it
    //access_token: String,

    //UNIX epoch timestamp for expiration
    expiration: usize,
}

impl OidcSession {
    pub fn expired(&self) -> bool {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs() as usize;
        now > self.expiration
    }
}

#[derive(Clone, Serialize, Deserialize, Default)]
pub struct CurrentUser(Option<String>);

impl CurrentUser {
    pub fn is_anonymous(&self) -> bool {
        self.0.is_none()
    }

    pub fn is_authenticated(&self) -> bool {
        self.0.is_some()
    }

    pub fn as_str(&self) -> &str {
        self.0.as_deref().unwrap_or("anonymous")
    }
}

type AuthState = (Arc<ServiceState>, isize); //holds state and endpoint index (positive numbers) or transfer ID (negative numbers)

impl ServiceState {
    /// We passed the endpoint_index as state in the original auth request, now we pick it up again
    /// so we can derive the actual endpoint to redrect to from it redirect_uri from it.
    /// This the 'state' field during authorization can either directly encode an endpoint_index (if it's >=0),
    /// or it references a transfer ID (negative number) that needs to be looked up in an internal map first
    pub(crate) fn endpoint_index_from_authstate(
        &self,
        state_value: isize,
    ) -> Result<usize, StatusCode> {
        if state_value >= 0 {
            //normal situation
            return Ok(state_value as usize);
        } else if let Ok(session_adoption_map) = self.session_adoption_map.read() {
            //valid transfer ID
            if let Some(projectkey) = session_adoption_map.get(&state_value) {
                return Ok(projectkey.endpoint_index());
            }
        }
        debug!("authentication state value is not a valid endpoint");
        Err(StatusCode::FORBIDDEN)
    }

    pub(crate) fn redirect_url_from_authstate(
        &self,
        state_value: isize,
    ) -> Result<String, StatusCode> {
        if state_value >= 0 {
            //normal situation
            return self.redirect_url(state_value as usize).ok_or({
                debug!("authentication state value is not a valid endpoint");
                StatusCode::FORBIDDEN
            });
        } else if let Ok(mut session_adoption_map) = self.session_adoption_map.write() {
            //valid transfer ID for an adoption
            if let Some(projectkey) = session_adoption_map.remove(&state_value) {
                debug!(
                    "authentication state value is a valid adoption, redirecting to adoption URL"
                );
                //redirect to adoption URL
                let adopt_url = format!(
                    "{}/adopt/{}/{}",
                    self.config().url().clone().unwrap_or_default(),
                    projectkey.user(),
                    projectkey.name()
                );
                return Ok(adopt_url);
            }
        }
        debug!("authentication state value does not correspond with an adoptable project");
        Err(StatusCode::FORBIDDEN)
    }

    /// Validated a OIDC Session ID (our own bookkeeping)
    pub fn validate_session_id(&self, session_id: &str) -> Option<String> {
        if let Ok(session_map) = self.openid_session_map.read() {
            if let Some(session) = session_map.get(session_id) {
                //check expiration
                if session.expired() {
                    debug!("OIDC Session expired");
                    return None;
                }
                debug!("OIDC authentication succeeded as {}", session.username);
                Some(session.username.clone())
            } else {
                debug!("OIDC authentication failed (invalid session id)");
                None
            }
        } else {
            panic!("Session lock poisoned!") //shouldn't happen
        }
    }
}

pub(crate) fn get_session_id(req: &Request) -> Option<&str> {
    if let Some(cookie_header) = req.headers().get(header::COOKIE) {
        for cookie in cookie_header.to_str().unwrap().split(";") {
            let mut iter = cookie.splitn(2, '=');
            if let (Some(name), Some(value)) = (iter.next(), iter.next()) {
                if name.trim() == "session_id" {
                    return Some(value.trim());
                }
            }
        }
    }
    None
}

/// Authentication middleware function
/// adds username to the request if login succesful
pub(crate) async fn auth(
    State((state, state_value)): State<AuthState>,
    mut req: Request,
    next: Next,
) -> Result<Response, StatusCode> {
    let endpoint_index = state.endpoint_index_from_authstate(state_value)?;
    let endpoint = state.endpoint(endpoint_index);
    let auth_header = req
        .headers()
        .get(header::AUTHORIZATION)
        .and_then(|h| h.to_str().ok());

    match auth_header {
        Some(auth) if auth.starts_with("Basic ") => {
            if let Some(user_id) = validate_basic_auth(&auth[6..], &state) {
                debug!(
                    "Basic authentication succeeded as {} (from header)",
                    user_id
                );
                req.extensions_mut().insert(CurrentUser(Some(user_id)));
                return Ok(next.run(req).await);
            } else {
                debug!("Basic authentication failed (header provided but failed check)");
                return Err(StatusCode::UNAUTHORIZED);
            }
        }
        Some(auth) if auth.starts_with("Bearer ") => {
            if let Some(username) = state.validate_session_id(auth[7..].trim()) {
                //validate_session_id will also output some debug info
                req.extensions_mut().insert(CurrentUser(Some(username)));
                return Ok(next.run(req).await);
            } else {
                debug!("Oidc validation based on headers failed, falling back to cookies next...");
            }
        }
        _ => {
            debug!("No authentication headers found in HTTP request, trying cookies next...");
        }
    };

    //no header supplied
    //fallback: get access token from cookie (to be expected for OIDC)
    let mut fail = false;
    if let Some(session_id) = get_session_id(&req) {
        if let Some(username) = state.validate_session_id(session_id) {
            //validate_session_id will also output some debug info
            req.extensions_mut().insert(CurrentUser(Some(username)));
            return Ok(next.run(req).await);
        } else {
            // session is invalid or expired, we need a new one
            fail = true;
        }
    }

    if endpoint.public()
        || (!fail && !state.oauthcredentials.enabled() && !state.basicauth_enabled())
    {
        // No authentication information supplied, that's okay
        // for public endpoints (or whenever no authentication is enabled for the entire service)
        // we are user 'anonymous'
        debug!("No authentication enabled/required here, anonymous login accepted...");
        req.extensions_mut().insert(CurrentUser(None));
        Ok(next.run(req).await)
    } else {
        //Not a public endpoint, we are unauthorized and need to login!

        if state.oauthcredentials.enabled() {
            debug!("Authentication required but not provided, redirecting to OIDC login");
            // Redirect to login page for OIDC
            Ok(ClamResponse::RedirectGet(format!(
                "{}/login/{}",
                state.config().url().as_deref().unwrap_or_default(),
                endpoint_index
            ))
            .into_response())
        } else {
            debug!(
                "Authentication required but not provided, requesting HTTP Basic Authentication"
            );
            Ok((
                StatusCode::UNAUTHORIZED,
                [(
                    header::WWW_AUTHENTICATE,
                    format!("Basic realm=\"{}\"", state.config().name()),
                )],
            )
                .into_response())
        }
    }
}

/// Validate HTTP Basic Authentication against the service's user database
fn validate_basic_auth(credentials: &str, state: &ServiceState) -> Option<String> {
    if let Ok(credentials) = STANDARD.decode(credentials.as_bytes()) {
        if let Ok(credentials) = std::str::from_utf8(&credentials) {
            let mut fields = credentials.splitn(2, ':');
            if let (Some(user), Some(password)) = (fields.next(), fields.next()) {
                // hash password (SHA256)
                let pwhash: String = Sha256::digest(
                    format!(
                        "{}{}",
                        state.config().auth().salt().as_deref().unwrap_or_default(),
                        password
                    )
                    .as_bytes(),
                )
                .iter()
                .map(|byte| format!("{byte:02x}"))
                .collect();
                //lookup in user database
                if let Ok(user_db) = state.user_db.read() {
                    if let Some(ref_pwhash) = user_db.get(user) {
                        if &ref_pwhash.to_lowercase() == &pwhash {
                            return Some(user.to_string());
                        }
                    }
                }
            }
        }
    }
    None
}

/// Validates an OIDC ID token, return the user's email as user identifier if possible, otherwise a unique subject ID
/// Returns None if validation did not succeed
async fn validate_id_token(token: &str, state: &ServiceState) -> Option<String> {
    //Decode the token header to find which key was used to sign it
    debug!("Validating OIDC token...");

    let header = match jsonwebtoken::decode_header(token) {
        Ok(h) => h,
        Err(e) => {
            debug!("error decoding json web token header: {}", e);
            return None;
        }
    };

    let key_id = match header.kid {
        Some(k) => k,
        None => {
            debug!("No key ID found");
            return None;
        }
    };

    // Look up the matching public key in our cached JWKS
    if let Some(jwkset) = state.jwkset.as_ref() {
        if let Some(jwk) = jwkset.find(&key_id) {
            match jwk.algorithm {
                jsonwebtoken::jwk::AlgorithmParameters::RSA(ref rsa) => {
                    let decoding_key =
                        match jsonwebtoken::DecodingKey::from_rsa_components(&rsa.n, &rsa.e) {
                            Ok(k) => k,
                            Err(e) => {
                                debug!("error decoding key: {}", e);
                                return None;
                            }
                        };

                    // Validate the token signature and claims
                    let mut validation = jsonwebtoken::Validation::new(header.alg);
                    validation.set_audience(&[&state.oauthcredentials.oauth_client_id]);
                    validation.set_issuer(&[state.openidconfig.as_ref().unwrap().issuer.as_str()]);

                    // We use serde_json::Value as a generic claims struct just to verify the signature
                    match jsonwebtoken::decode::<OidcClaims>(token, &decoding_key, &validation) {
                        Ok(token_data) => {
                            // Return email if available, otherwise fall back to the subject string namespaced by the provider
                            debug!("...success");

                            if token_data.claims.email_verified == Some(true) {
                                if let Some(email) = token_data.claims.email {
                                    return Some(email);
                                }
                            }

                            // fallback username, usually we should namespace the subject ID with
                            // claims.iss but we only allow one provider anyway and using it means
                            // we trust the issuer
                            return Some(token_data.claims.sub);
                        }
                        Err(e) => {
                            debug!("error decoding/verifying json web token: {}", e);
                        }
                    }
                }
                _ => {
                    error!(
                        "OIDC provider uses an algorithm we have not implemented! (only RSA is supported)"
                    );
                }
            }
        }
    }
    debug!("...failed");
    None
}

/// Initiate the login process by redirecting to the authorization endpoint
pub(crate) async fn login_handler(
    State(state): State<Arc<ServiceState>>,
    Path(endpoint_index): Path<usize>,
) -> Response {
    if let Some(openidconfig) = state.openidconfig.as_ref() {
        let scope: String = state.oauthcredentials.oauth_scope.join("%20");
        let auth_url = format!(
            "{}?response_type=code&client_id={}&redirect_uri={}&scope={}&state={}",
            openidconfig.authorization_endpoint,
            state.oauthcredentials.oauth_client_id,
            state.openid_redirect_url.as_ref().unwrap(),
            scope,
            endpoint_index, //this is the state, it will be send back to the callback and will redirect us once more to the final destination
        );
        Redirect::temporary(&auth_url).into_response()
    } else {
        ApiError::NotFound("OAuth2 login endpoint is not enabled on this service".into())
            .into_json_response()
    }
}

/// Log the user out by forgetting the session
pub(crate) async fn logout_handler(
    State(state): State<Arc<ServiceState>>,
    jar: CookieJar,
    req: Request,
) -> Response {
    if state.openidconfig.is_some() {
        // Remove the session
        if let Some(session_id) = get_session_id(&req) {
            if let Ok(mut session_map) = state.openid_session_map.write() {
                session_map.remove(session_id);
            } else {
                error!("OIDC Session lock poisoned");
                return (
                    StatusCode::INTERNAL_SERVER_ERROR,
                    "OIDC session lock poisoined",
                )
                    .into_response();
            }
        }

        // Remove the cookie and redirect back to landing page
        let redirect_url = state.config().url().as_deref().unwrap_or("/");
        (jar.remove("session_id"), Redirect::temporary(&redirect_url)).into_response()
    } else {
        //no OIDC, basic authentication has no real logout, return 401 in an attempt to make the browser forget the credentials
        return (
            StatusCode::UNAUTHORIZED,
            format!(
                "Attempting logout even though HTTP Basic Authentication has no real logout mechanism, click <a href=\"{}\">here</a> to continue and clear browser data if this did not work.",
                state.config().url().as_deref().unwrap_or("/")
            ),
        ).into_response();
    }
}

// Get OpenID Configuration from the Identity Service Provider
pub fn get_openid_config(url: &str) -> Result<OpenIdConfiguration, String> {
    debug!("Obtaining OpenID configuration from {}", url);
    match ureq::get(url).call() {
        Ok(mut response) => response
            .body_mut()
            .read_json::<OpenIdConfiguration>()
            .map_err(|e| format!("Failed to parse OpenID Configuration: {}", e)),
        Err(e) => Err(format!(
            "Failed to obtain OpenID Configuration from identity provider: {}",
            e
        )),
    }
}

// Get JSON Web Key Set
pub fn get_jwks(url: &str) -> jsonwebtoken::jwk::JwkSet {
    let mut response = ureq::get(url)
        .call()
        .expect("Failed to obtain JSON Web Token Set from identity provider");
    response
        .body_mut()
        .read_json::<jsonwebtoken::jwk::JwkSet>()
        .expect("Failed to parse JWKS")
}

/// Handles the callback and exchanges the code for a token
pub async fn callback_handler(
    State(state): State<Arc<ServiceState>>,
    jar: CookieJar,
    Query(auth_req): Query<AuthRequest>,
) -> Result<(CookieJar, Redirect), StatusCode> {
    if let Some(openidconfig) = state.openidconfig.as_ref() {
        // we passed the endpoint_index as state in the original auth request, the following
        // function picks it up again and also handled adopted (if a transfer ID was passed as state
        // instead of an endpoint_index)
        let redirect_uri = state.redirect_url_from_authstate(auth_req.state)?;

        let client = reqwest::Client::new();

        let state_as_str = format!("{}", auth_req.state);
        let params = [
            ("grant_type", "authorization_code"),
            ("code", &auth_req.code),
            (
                "redirect_uri",
                state
                    .openid_redirect_url
                    .as_ref()
                    .expect("openid_redirect_url should have been computed earlier"),
            ),
            ("state", &state_as_str),
        ];

        let res = match client
            .post(openidconfig.token_endpoint.as_str())
            .form(&params)
            .basic_auth(
                state.oauthcredentials.oauth_client_id.as_str(),
                Some(state.oauthcredentials.oauth_client_secret.as_str()),
            )
            .send()
            .await
        {
            Ok(res) => res,
            Err(e) => {
                error!(
                    "Failed to contact OpenID provider for token verification: {}",
                    e
                );
                return Err(StatusCode::INTERNAL_SERVER_ERROR);
            }
        };

        if res.status().is_success() {
            let token_data: TokenResponse = match res.json().await {
                Ok(token_data) => token_data,
                Err(e) => {
                    error!(
                        "Failed to parse JSON token response from OpenID provider: {}",
                        e
                    );
                    return Err(StatusCode::INTERNAL_SERVER_ERROR);
                }
            };

            if token_data.id_token.is_none() {
                debug!("ID token verification failed",);
                return Err(StatusCode::UNAUTHORIZED);
            }

            if token_data.id_token.is_none() {
                error!("Failed to obtain ID token from  OpenID provider");
                return Err(StatusCode::INTERNAL_SERVER_ERROR);
            }

            //validate id_token and get username (email or fallback)
            let mut username =
                match validate_id_token(token_data.id_token.as_deref().unwrap(), &state).await {
                    Some(u) => u,
                    None => {
                        error!("ID token verification failed");
                        return Err(StatusCode::UNAUTHORIZED);
                    }
                };

            if openidconfig.userinfo_endpoint.is_none() {
                error!("No userinfo endpoint known");
                return Err(StatusCode::INTERNAL_SERVER_ERROR);
            }

            //query userinfo endpoint for username (email actually) if what we got thus-far doesn't look like an email address (very crude check)
            if !username.chars().any(|c| c == '@') {
                match client
                    .get(openidconfig.userinfo_endpoint.as_deref().unwrap())
                    .bearer_auth(token_data.access_token)
                    .send()
                    .await
                {
                    Ok(res) => match res.json::<OidcClaims>().await {
                        Ok(userinfo_data) => match userinfo_data.email {
                            Some(email) => username = email,
                            None => {
                                warn!(
                                    "Userinfo reply from OpenID provider did not contain an email address, received: {:?}",
                                    userinfo_data
                                );
                            }
                        },
                        Err(e) => {
                            error!(
                                "Failed to decode userinfo JSON response from OpenID provider: {}",
                                e
                            );
                            return Err(StatusCode::INTERNAL_SERVER_ERROR);
                        }
                    },
                    Err(e) => {
                        error!(
                            "Failed to contact OpenID provider for userinfo verification: {}",
                            e
                        );
                        return Err(StatusCode::INTERNAL_SERVER_ERROR);
                    }
                };
            }

            // Now we create a session
            let session_id: String = Uuid::new_v4().into();
            if let Ok(mut session_map) = state.openid_session_map.write() {
                let now = SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .unwrap()
                    .as_secs() as usize;
                session_map.insert(
                    session_id.clone(),
                    OidcSession {
                        username,
                        expiration: now + token_data.expires_in as usize,
                    },
                );
            } else {
                error!("OIDC Session lock poisoned");
                return Err(StatusCode::INTERNAL_SERVER_ERROR);
            }

            // And we hand the session id to the user
            let mut cookie = Cookie::new("session_id", session_id);
            cookie.set_path(state.oauthcredentials.cookie_path().clone());
            cookie.set_http_only(true);
            cookie.set_secure(true); // https only
            cookie.set_same_site(axum_extra::extract::cookie::SameSite::Lax); // Protects against CSRF, 'Strict' interferes with login flow

            // Add the cookie to the jar
            let updated_jar = jar.add(cookie);
            debug!(
                "Login successful, adding authentication cookie and redirecting to {}",
                redirect_uri
            );

            // Redirect to the actually requested endpoint
            Ok((updated_jar, Redirect::to(redirect_uri.as_str())))
        } else {
            debug!(
                "OIDC token verification failed with error {}: {}",
                res.status(),
                res.text().await.unwrap()
            );
            Err(StatusCode::UNAUTHORIZED)
        }
    } else {
        debug!("OIDC callback endpoint was called but not enabled");
        Err(StatusCode::FORBIDDEN)
    }
}

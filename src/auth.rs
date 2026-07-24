use crate::error::ApiError;
use crate::state::ServiceState;
use axum::extract::Request;
use axum::extract::{Query, State};
use axum::http::{StatusCode, header};
use axum::middleware::Next;
use axum::response::Response;
use axum::response::{IntoResponse, Redirect};
use axum_extra::extract::cookie::{Cookie, CookieJar};
use base64::{Engine as _, engine::general_purpose::STANDARD};
use serde::{Deserialize, Serialize};
use std::sync::Arc;

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
}

#[derive(Deserialize)]
struct OidcClaims {
    // The standard OIDC claim for user emails
    email: Option<String>,
    // Fallback unique identifier if email isn't present
    sub: String,
}

#[derive(Serialize, Deserialize)]
pub struct TokenResponse {
    access_token: String,
    id_token: Option<String>,
    token_type: String,
    expires_in: i64,
}

#[derive(Clone, Serialize, Deserialize)]
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

/// Authentication middleware function
/// adds username to the request if login succesful
pub(crate) async fn auth(
    state: State<Arc<ServiceState>>,
    mut req: Request,
    next: Next,
) -> Result<Response, StatusCode> {
    let auth_header = req
        .headers()
        .get(header::AUTHORIZATION)
        .and_then(|h| h.to_str().ok());

    match auth_header {
        Some(auth) if auth.starts_with("Basic ") => {
            if let Some(user_id) = validate_basic_auth(&auth[6..], &state) {
                req.extensions_mut().insert(CurrentUser(Some(user_id)));
                return Ok(next.run(req).await);
            } else {
                return Err(StatusCode::UNAUTHORIZED);
            }
        }
        Some(auth) if auth.starts_with("Bearer ") => {
            if let Some(user_id) = validate_oidc_token(&auth[7..], &state).await {
                req.extensions_mut().insert(CurrentUser(Some(user_id)));
                return Ok(next.run(req).await);
            } else {
                return Err(StatusCode::UNAUTHORIZED);
            }
        }
        None => {
            //No authentication header supplied, we are 'anonymous'
            req.extensions_mut().insert(CurrentUser(None));
        }
        _ => {}
    };

    //fallback: get OIDC token from cookie
    if let Some(cookie_header) = req.headers().get(header::COOKIE) {
        for cookie in cookie_header.to_str().unwrap().split(";") {
            let mut iter = cookie.splitn(2, '=');
            if let (Some(name), Some(value)) = (iter.next(), iter.next()) {
                if name.trim() == "auth_token" {
                    if let Some(user_id) = validate_oidc_token(value.trim(), &state).await {
                        req.extensions_mut().insert(CurrentUser(Some(user_id)));
                        return Ok(next.run(req).await);
                    } else {
                        return Err(StatusCode::UNAUTHORIZED);
                    }
                }
            }
        }
    }

    //no authentication supplied, we are anonymous
    req.extensions_mut().insert(CurrentUser(None));
    return Ok(next.run(req).await);
}

/// Validate HTTP Basic Authentication against the service's user database
fn validate_basic_auth(credentials: &str, state: &ServiceState) -> Option<String> {
    if let Ok(credentials) = STANDARD.decode(credentials.as_bytes()) {
        if let Ok(credentials) = std::str::from_utf8(&credentials) {
            let mut fields = credentials.splitn(2, ':');
            if let (Some(user), Some(pwhash)) = (fields.next(), fields.next()) {
                //lookup in user database
                if let Ok(user_db) = state.user_db.read() {
                    if let Some(ref_pwhash) = user_db.get(user) {
                        if ref_pwhash == pwhash {
                            return Some(user.to_string());
                        }
                    }
                }
            }
        }
    }
    None
}

/// Validates an OIDC token, return the user's email as user identifier if possible, otherwise a unique subject ID
/// Returns None if validation did not succeed
async fn validate_oidc_token(token: &str, state: &ServiceState) -> Option<String> {
    //Decode the token header to find which key was used to sign it
    let header = match jsonwebtoken::decode_header(token) {
        Ok(h) => h,
        Err(_) => return None,
    };

    let key_id = match header.kid {
        Some(k) => k,
        None => return None,
    };

    // Look up the matching public key in our cached JWKS
    if let Some(jwkset) = state.jwkset.as_ref() {
        if let Some(jwk) = jwkset.find(&key_id) {
            match jwk.algorithm {
                jsonwebtoken::jwk::AlgorithmParameters::RSA(ref rsa) => {
                    let decoding_key =
                        match jsonwebtoken::DecodingKey::from_rsa_components(&rsa.n, &rsa.e) {
                            Ok(k) => k,
                            Err(_) => return None,
                        };

                    // Validate the token signature and claims
                    let mut validation = jsonwebtoken::Validation::new(header.alg);
                    validation.set_audience(&[&state.oauthcredentials.oauth_client_id]);
                    validation.set_issuer(&[state.openidconfig.as_ref().unwrap().issuer.as_str()]);

                    // We use serde_json::Value as a generic claims struct just to verify the signature
                    if let Ok(token_data) =
                        jsonwebtoken::decode::<OidcClaims>(token, &decoding_key, &validation)
                    {
                        // Return email if available, otherwise fall back to the subject string
                        return Some(token_data.claims.email.unwrap_or(token_data.claims.sub));
                    }
                }
                _ => {
                    eprintln!(
                        "WARNING: OIDC provider uses an algorithm we have not implemented! (only RSA is supported)"
                    );
                }
            }
        }
    }
    None
}

/// Initiate the login process by redirecting to the authorization endpoint
pub(crate) async fn login_handler(State(state): State<Arc<ServiceState>>) -> Response {
    if let Some(openidconfig) = state.openidconfig.as_ref() {
        let scope: String = state.oauthcredentials.oauth_scope.join("%20");
        let auth_url = format!(
            "{}?response_type=code&client_id={}&redirect_uri={}&scope={}",
            openidconfig.authorization_endpoint,
            state.oauthcredentials.oauth_client_id,
            state.oauthcredentials.openid_redirect_url,
            scope
        );
        Redirect::temporary(&auth_url).into_response()
    } else {
        ApiError::NotFound("OAuth2 login endpoint is not enabled on this service".into())
            .into_response()
    }
}

// Get OpenID Configuration from the Identity Service Provider
pub fn get_openid_config(url: &str) -> OpenIdConfiguration {
    let response = reqwest::blocking::get(url)
        .expect("Failed to obtain OpenID Configuration from identity provider");
    response
        .json()
        .expect("Failed to parse OpenID Configuration")
}

// Get JSON Web Key Set
pub fn get_jwks(url: &str) -> jsonwebtoken::jwk::JwkSet {
    let response = reqwest::blocking::get(url)
        .expect("Failed to obtain JSON Web Token Set from identity provider");
    response.json().expect("Failed to parse JWKS")
}

/// Handles the callback and exchanges the code for a token
pub async fn callback_handler(
    State(state): State<Arc<ServiceState>>,
    jar: CookieJar,
    Query(auth_req): Query<AuthRequest>,
) -> Result<(CookieJar, Redirect), StatusCode> {
    if let Some(openidconfig) = state.openidconfig.as_ref() {
        let client = reqwest::Client::new();

        let params = [
            ("grant_type", "authorization_code"),
            ("code", &auth_req.code),
            ("client_id", state.oauthcredentials.oauth_client_id.as_str()),
            (
                "client_secret",
                state.oauthcredentials.oauth_client_secret.as_str(),
            ),
            (
                "redirect_uri",
                state.oauthcredentials.openid_redirect_url.as_str(),
            ),
        ];

        let res = client
            .post(openidconfig.token_endpoint.as_str())
            .form(&params)
            .send()
            .await
            .expect("Failed to send token request");

        if res.status().is_success() {
            let token_data: TokenResponse = res.json().await.unwrap();

            //Build session cookie with the OIDC token
            let mut cookie = Cookie::new("auth_token", token_data.access_token);
            cookie.set_path(state.oauthcredentials.cookie_path().clone());
            cookie.set_http_only(true);
            cookie.set_secure(true); // https only
            cookie.set_same_site(axum_extra::extract::cookie::SameSite::Lax); // Protects against CSRF

            // Add the cookie to the jar
            let updated_jar = jar.add(cookie);

            // Redirect
            if let Some(url) = state.config().url() {
                return Ok((updated_jar, Redirect::to(url)));
            } else {
                return Ok((
                    updated_jar,
                    Redirect::to(state.oauthcredentials.cookie_path()),
                ));
            }
        }
    }
    Err(StatusCode::UNAUTHORIZED)
}

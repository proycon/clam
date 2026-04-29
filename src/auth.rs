use crate::state::ServiceState;
use axum::extract::Request;
use axum::extract::State;
use axum::http::{StatusCode, header};
use axum::middleware::Next;
use axum::response::Response;
use base64::{Engine as _, engine::general_purpose::STANDARD};
use std::sync::Arc;

pub(crate) async fn auth(
    state: State<Arc<ServiceState>>,
    req: Request,
    next: Next,
) -> Result<Response, StatusCode> {
    let auth_header = req
        .headers()
        .get(header::AUTHORIZATION)
        .and_then(|h| h.to_str().ok());

    match auth_header {
        Some(auth) if auth.starts_with("Basic ") => {
            if validate_basic_auth(&auth[6..]) {
                Ok(next.run(req).await)
            } else {
                Err(StatusCode::UNAUTHORIZED)
            }
        }
        Some(auth) if auth.starts_with("Bearer ") => {
            if validate_oidc_token(&auth[7..]).await {
                Ok(next.run(req).await)
            } else {
                Err(StatusCode::UNAUTHORIZED)
            }
        }
        _ => Err(StatusCode::UNAUTHORIZED),
    }
}

fn validate_basic_auth(credentials: &str) -> bool {
    if let Ok(credentials) = STANDARD.decode(credentials.as_bytes()) {
        if let Ok(credentials) = std::str::from_utf8(&credentials) {
            let mut fields = credentials.splitn(2, ':');
            if let (Some(user), Some(pwhash)) = (fields.next(), fields.next()) {
                //lookup in user database
                todo!();
                return true;
            }
        }
    }
    false
}

async fn validate_oidc_token(token: &str) -> bool {
    // Fetch JWKS from OIDC provider
    // Use `jsonwebtoken` to decode and validate
    todo!();
    true
}

use crate::config::EndPointMode;
use crate::config::{EndPoint, ServiceConfig};
use crate::dispatcher::{Dispatcher, Message};
use crate::error::{ApiError, ClamError};
use crate::job::Job;
use crate::state::ServiceState;
use tokio::signal;
use tower_http::trace::TraceLayer;

use axum::Router;
use axum::body::Body;
use axum::extract::State;
use axum::http::{HeaderMap, HeaderValue, Request, StatusCode, header};
use axum::response::{IntoResponse, Json, Response};
use axum::routing::{delete, get, post, put};
use serde_json::Value;
use std::sync::{Arc, mpsc::Sender};

const CONTENT_TYPE_JSON: &str = "application/json";
const CONTENT_TYPE_HTML: &str = "text/html";

pub struct Service {
    config: ServiceConfig,
    dispatchersender: Option<Sender<Message>>,
}

pub enum ClamResponse {
    Ok(),
    Created(),
    NoContent(),
    Text(String),
    Body { stream: Body, contenttype: String },
    JsonList(Vec<Value>),
}

impl IntoResponse for ClamResponse {
    fn into_response(self) -> Response {
        let cors = (
            header::ACCESS_CONTROL_ALLOW_ORIGIN,
            HeaderValue::from_static("*"),
        );
        let server = (
            header::SERVER,
            HeaderValue::from_str(crate::SERVER).unwrap(),
        );
        match self {
            Self::Ok() => (StatusCode::OK, [cors, server], "ok").into_response(),
            Self::Created() => (StatusCode::CREATED, [cors, server], "created").into_response(),
            Self::NoContent() => {
                (StatusCode::NO_CONTENT, [cors, server], "deleted").into_response()
            }
            Self::Text(s) => (
                StatusCode::OK,
                [
                    cors,
                    server,
                    (
                        header::CONTENT_TYPE,
                        HeaderValue::from_str("text/plain; charset=utf-8").unwrap(),
                    ),
                ],
                s,
            )
                .into_response(),
            Self::Body {
                stream,
                contenttype,
            } => (
                StatusCode::OK,
                [
                    cors,
                    server,
                    (
                        header::CONTENT_TYPE,
                        HeaderValue::from_str(contenttype.as_str()).unwrap(),
                    ),
                ],
                stream,
            )
                .into_response(),
            Self::JsonList(data) => (StatusCode::OK, [cors, server], Json(data)).into_response(),
        }
    }
}

impl Service {
    pub fn new(config: ServiceConfig) -> Self {
        // create the dispatcher and set up communication channels
        Self {
            config,
            dispatchersender: None,
        }
    }

    #[tokio::main]
    pub async fn run(&self) {
        let bind = self.config.listen().as_deref().unwrap_or("127.0.0.1:8080");
        eprintln!("[clamservice] listening on {}", bind);
        let listener = tokio::net::TcpListener::bind(bind).await.unwrap();

        let dispatcher = Dispatcher::new(self.config.clone());
        //launch the dispatcher/job manager as a background thread
        //this is a non-blocking function that spawns the thread and returns immediately
        let state: Arc<ServiceState> = dispatcher.state(); //the dispatcher initiates the state for us
        dispatcher.spawn(); //consumes the dispatcher

        let mut router = Router::new();
        for endpoint in self.config.endpoints().iter() {
            router = self.configure_endpoint(router, endpoint);
        }
        let router = router
            //.merge(SwaggerUi::new("/swagger-ui").url("/api-doc/openapi.json", ApiDoc::openapi()))
            .layer(TraceLayer::new_for_http())
            .with_state(state.clone());

        axum::serve(listener, router.into_make_service())
            .with_graceful_shutdown(shutdown_signal(state))
            .await
            .unwrap();
    }

    pub fn configure_endpoint(
        &self,
        router: Router<Arc<ServiceState>>,
        endpoint: &EndPoint,
    ) -> Router<Arc<ServiceState>> {
        match endpoint.mode() {
            EndPointMode::Porch => router.route(endpoint.path(), get(porch)),
            EndPointMode::Project => {
                todo!();
            }
            EndPointMode::Action { filetype } => {
                todo!();
            }
        }
    }
}

async fn porch(
    state: State<Arc<ServiceState>>,
    request: Request<Body>,
) -> Result<ClamResponse, ApiError> {
    match negotiate_content_type(request.headers(), &[CONTENT_TYPE_JSON, CONTENT_TYPE_HTML]) {
        Ok(CONTENT_TYPE_JSON) => {
            todo!();
        }
        _ => Err(ApiError::NotAcceptable(
            "Accept header could not be satisfied (try application/json)",
        )),
    }
}

async fn action(
    state: State<Arc<ServiceState>>,
    request: Request<Body>,
) -> Result<ClamResponse, ApiError> {
    match negotiate_content_type(request.headers(), &[CONTENT_TYPE_JSON, CONTENT_TYPE_HTML]) {
        Ok(CONTENT_TYPE_JSON) => {
            todo!();
        }
        _ => Err(ApiError::NotAcceptable(
            "Accept header could not be satisfied (try application/json)",
        )),
    }
}

async fn shutdown_signal(state: Arc<ServiceState>) {
    let ctrl_c = async {
        signal::ctrl_c()
            .await
            .expect("failed to install Ctrl+C handler");
    };

    #[cfg(unix)]
    let terminate = async {
        signal::unix::signal(signal::unix::SignalKind::terminate())
            .expect("failed to install signal handler")
            .recv()
            .await;
    };

    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        _ = ctrl_c => {
        }
        _ = terminate => {
        }
    }
}

fn negotiate_content_type(
    headers: &HeaderMap<HeaderValue>,
    offer_types: &[&'static str],
) -> Result<&'static str, ApiError> {
    if let Some(accept_types) = headers.get(axum::http::header::ACCEPT) {
        let mut match_accept_index = None;
        let mut matching_offer = None;
        for (i, accept_type) in accept_types
            .to_str()
            .map_err(|_| ApiError::NotAcceptable("Invalid Accept header"))
            .unwrap_or(CONTENT_TYPE_JSON)
            .split(",")
            .enumerate()
        {
            let accept_type = accept_type.split(";").next().unwrap();
            for offer_type in offer_types.iter() {
                if *offer_type == accept_type
                    || accept_type == "*/*"
                        && (match_accept_index.is_none()
                            || (match_accept_index.is_some() && match_accept_index.unwrap() > i))
                {
                    match_accept_index = Some(i);
                    matching_offer = Some(*offer_type);
                }
            }
        }
        if let Some(matching_offer) = matching_offer {
            Ok(matching_offer)
        } else {
            Err(ApiError::NotAcceptable("No matching content type on offer"))
        }
    } else {
        Ok(offer_types[0])
    }
}

use crate::ResponseMessage;
use crate::auth::{CurrentUser, auth, callback_handler, login_handler};
use crate::config::EndPointMode;
use crate::config::{EndPoint, ServiceConfig};
use crate::dispatcher::{Dispatcher, Message};
use crate::error::{ApiError, ClamError};
use crate::job::Job;
use crate::project::{Project, ProjectStatus, project_index};
use crate::state::ServiceState;
use tokio::signal;
use tokio::sync::oneshot;
use tower_http::trace::TraceLayer;

use axum::Extension;
use axum::Router;
use axum::body::Body;
use axum::extract::{Path, State};
use axum::http::{HeaderMap, HeaderValue, Request, StatusCode, header};
use axum::middleware::from_fn_with_state;
use axum::response::{IntoResponse, Json, Response};
use axum::routing::{delete, get, post, put};
use serde_json::Value;
use std::sync::{Arc, mpsc::Sender};

const CONTENT_TYPE_JSON: &str = "application/json";
const CONTENT_TYPE_HTML: &str = "text/html";

pub struct Service {
    config: ServiceConfig,
}

pub enum ClamResponse {
    Ok(),
    Created(),
    NoContent(),
    Text(String),
    Body { stream: Body, contenttype: String },
    ProjectResponse(ProjectStatus),
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
            Self::ProjectResponse(status) => {
                (StatusCode::OK, [cors, server], Json(status)).into_response()
            }
        }
    }
}

impl Service {
    pub fn new(config: ServiceConfig) -> Self {
        // create the dispatcher and set up communication channels
        Self { config }
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

        let mut private_routes = Router::new();
        let mut public_routes = Router::new()
            .route("/login", get(login_handler))
            .route("/oidc/callback", get(callback_handler))
            .route("/openapi.json", get(get_api)) //openAPI endpoint
            .route("/info", get(get_info)); //wrapped around, openAPI endpoint, may serve swagger UI
        for (i, endpoint) in self.config.endpoints().iter().enumerate() {
            if endpoint.public() {
                public_routes = self.configure_endpoint(public_routes, i, endpoint);
            } else {
                private_routes = self.configure_endpoint(private_routes, i, endpoint);
            }
        }

        let router = Router::new()
            .merge(private_routes)
            .merge(public_routes)
            //.merge(SwaggerUi::new("/swagger-ui").url("/api-doc/openapi.json", ApiDoc::openapi()))
            .layer(TraceLayer::new_for_http())
            .route_layer(from_fn_with_state(state.clone(), |state, req, next| {
                auth(state, req, next)
            }))
            .with_state(state.clone());

        axum::serve(listener, router.into_make_service())
            .with_graceful_shutdown(shutdown_signal(state))
            .await
            .unwrap();
    }

    pub fn configure_endpoint(
        &self,
        mut router: Router<Arc<ServiceState>>,
        endpoint_index: usize,
        endpoint: &EndPoint,
    ) -> Router<Arc<ServiceState>> {
        match endpoint.mode() {
            EndPointMode::Porch => router.route(endpoint.path(), get(get_porch)),
            EndPointMode::Index => router.route(endpoint.path(), get(get_index)),
            EndPointMode::Project => {
                let index_path = format!("{}/projects", endpoint.path());
                router = router
                    .route(index_path.as_str(), get(get_projects))
                    .layer(Extension(endpoint_index));
                let path = format!("{}/{{project}}", endpoint.path());
                router = router
                    .route(path.as_str(), get(get_project))
                    .layer(Extension(endpoint_index));
                router = router
                    .route(path.as_str(), put(create_project))
                    .layer(Extension(endpoint_index));
                router = router
                    .route(path.as_str(), delete(delete_project))
                    .layer(Extension(endpoint_index));
                router = router
                    .route(path.as_str(), post(submit_project))
                    .layer(Extension(endpoint_index));

                //File uploading endpoints within a project
                let fpath = format!("{}/{{project}}/{{filename}}", endpoint.path());
                router = router
                    .route(fpath.as_str(), get(download_file))
                    .layer(Extension(endpoint_index));
                router = router
                    .route(fpath.as_str(), put(upload_file))
                    .layer(Extension(endpoint_index));
                router = router
                    .route(fpath.as_str(), delete(delete_file))
                    .layer(Extension(endpoint_index));
                router
            }
            EndPointMode::Action => {
                // Both GET or POST are fine for actions
                router = router
                    .route(endpoint.path(), get(get_action))
                    .layer(Extension(endpoint_index));
                router = router.route(
                    endpoint.path(),
                    post(post_action).layer(Extension(endpoint_index)),
                );
                router
            }
        }
    }
}

async fn get_api(state: State<Arc<ServiceState>>) -> Result<ClamResponse, ApiError> {
    match state.openapi.to_json() {
        Ok(apidoc) => {
            return Ok(ClamResponse::Body {
                stream: apidoc.into(),
                contenttype: "application/json".to_string(),
            });
        }
        Err(e) => {
            eprintln!("ERROR serialising OpenAPI specification: {}", e);
            Err(ApiError::InternalError(
                "Internal error whilst serializing OpenAPI specification to JSON, check server logs for details",
            ))
        }
    }
}

async fn get_info(
    state: State<Arc<ServiceState>>,
    request: Request<Body>,
) -> Result<ClamResponse, ApiError> {
    match negotiate_content_type(request.headers(), &[CONTENT_TYPE_JSON, CONTENT_TYPE_HTML]) {
        Ok(CONTENT_TYPE_JSON) => get_api(state).await,
        Ok(CONTENT_TYPE_HTML) => {
            //present swagger UI
            todo!();
        }
        _ => Err(ApiError::NotAcceptable(
            "Accept header could not be satisfied (try application/json)",
        )),
    }
}

async fn get_porch(
    state: State<Arc<ServiceState>>,
    Extension(endpoint_index): Extension<usize>,
    request: Request<Body>,
) -> Result<ClamResponse, ApiError> {
    let endpoint = state.endpoint(endpoint_index);
    match negotiate_content_type(request.headers(), &[CONTENT_TYPE_JSON, CONTENT_TYPE_HTML]) {
        Ok(CONTENT_TYPE_JSON) => get_api(state).await,
        Ok(CONTENT_TYPE_HTML) => {
            //present human-readable welcome porch
            todo!();
        }
        _ => Err(ApiError::NotAcceptable(
            "Accept header could not be satisfied (try application/json)",
        )),
    }
}

/// Index of endpoints (actions & project endpoint with project list). The user will be directed here after login.
async fn get_index(
    state: State<Arc<ServiceState>>,
    Extension(endpoint_index): Extension<usize>,
    request: Request<Body>,
) -> Result<ClamResponse, ApiError> {
    let endpoint = state.endpoint(endpoint_index);
    match negotiate_content_type(request.headers(), &[CONTENT_TYPE_JSON, CONTENT_TYPE_HTML]) {
        Ok(CONTENT_TYPE_JSON) => get_api(state).await,
        Ok(CONTENT_TYPE_HTML) => {
            //present human-readable list of actions and project endpoints, as well as the actual projects there (calls project_index() for each)
            todo!();
        }
        _ => Err(ApiError::NotAcceptable(
            "Accept header could not be satisfied (try application/json)",
        )),
    }
}

/// Presents a list of projects for a given user and endpoint (Web API only, humans only use get_index)
async fn get_projects(
    Extension(endpoint_index): Extension<usize>,
    state: State<Arc<ServiceState>>,
    headers: HeaderMap,
    request: Request<Body>,
) -> Result<ClamResponse, ApiError> {
    let endpoint = state.endpoint(endpoint_index);
    let username = get_username(&headers);
    match negotiate_content_type(request.headers(), &[CONTENT_TYPE_JSON, CONTENT_TYPE_HTML]) {
        Ok(CONTENT_TYPE_JSON) => {
            //return project list (for actions the OpenAPI endpoint already suffices)
            if let Ok(projects) = project_index(username, endpoint, state.config()) {
                Ok(ClamResponse::JsonList(
                    projects.into_iter().map(|project| project.into()).collect(),
                ))
            } else {
                Err(ApiError::InternalError("Unable to obtain project list"))
            }
        }
        Ok(CONTENT_TYPE_HTML) => {
            //present human-readable welcome porch with project and action list
            //(I'm not sure if I'll actually use this or enumerate all projects from all endpoints on the index page)
            todo!();
        }
        _ => Err(ApiError::NotAcceptable(
            "Accept header could not be satisfied (try application/json)",
        )),
    }
}

async fn get_project(
    Path(project): Path<String>,
    Extension(endpoint_index): Extension<usize>,
    state: State<Arc<ServiceState>>,
    headers: HeaderMap,
    request: Request<Body>,
) -> Result<ClamResponse, ApiError> {
    let endpoint = state.endpoint(endpoint_index);
    if let Ok(project) = Project::new(project, get_username(&headers), endpoint.path()) {
        match negotiate_content_type(request.headers(), &[CONTENT_TYPE_JSON, CONTENT_TYPE_HTML]) {
            Ok(CONTENT_TYPE_JSON) => {
                //present staging stage, progress stage or output stage (including index of input/output files for the first and last)
                // build ProjectStatus and return ClamResponse::ProjectResponse(ProjectStatus) as response
                todo!();
            }
            Ok(CONTENT_TYPE_HTML) => {
                //present staging interface, in progress message, or output interface, depending on project state
                todo!();
            }
            _ => Err(ApiError::NotAcceptable(
                "Accept header could not be satisfied (try application/json)",
            )),
        }
    } else {
        Err(ApiError::InvalidName("project name invalid"))
    }
}

async fn submit_project(
    Path(project): Path<String>,
    Extension(endpoint_index): Extension<usize>,
    Extension(user): Extension<CurrentUser>,
    state: State<Arc<ServiceState>>,
    headers: HeaderMap,
    request: Request<Body>,
) -> Result<ClamResponse, ApiError> {
    let job = Job::new(&state, endpoint_index, Some(project), &user, &headers);
    let (tx, rx) = oneshot::channel();
    state.send(Message::SubmitJob(job, tx));
    match rx.await {
        Ok(ResponseMessage::JobSubmitted) => Ok(ClamResponse::Ok()),
        Ok(ResponseMessage::JobError(error)) => Err(ApiError::ServiceUnavailable(error)),
        Err(_) => Err(ApiError::InternalError(
            "oneshot sender dropped whilst submitting a job",
        )),
        Ok(_) => Err(ApiError::InternalError(
            "unexpected response message whilst submitting a job",
        )),
    }
}

async fn create_project(
    Path(project): Path<String>,
    Extension(endpoint_index): Extension<usize>,
    state: State<Arc<ServiceState>>,
    headers: HeaderMap,
    request: Request<Body>,
) -> Result<ClamResponse, ApiError> {
    let endpoint = state.endpoint(endpoint_index);
    match negotiate_content_type(request.headers(), &[CONTENT_TYPE_JSON]) {
        Ok(CONTENT_TYPE_JSON) => {
            if let Ok(project) = Project::new(project, get_username(&headers), endpoint.path()) {
                if let Err(e) = project.create(state.config()) {
                    Err(e.into())
                } else {
                    Ok(ClamResponse::Created())
                }
            } else {
                Err(ApiError::InvalidName("project name invalid"))
            }
        }
        _ => Err(ApiError::NotAcceptable(
            "Accept header could not be satisfied (try application/json)",
        )),
    }
}

async fn delete_project(
    Path(project): Path<String>,
    Extension(endpoint_index): Extension<usize>,
    state: State<Arc<ServiceState>>,
    headers: HeaderMap,
    request: Request<Body>,
) -> Result<ClamResponse, ApiError> {
    let endpoint = state.endpoint(endpoint_index);
    match negotiate_content_type(request.headers(), &[CONTENT_TYPE_JSON]) {
        Ok(CONTENT_TYPE_JSON) => {
            if let Ok(project) = Project::new(project, get_username(&headers), endpoint.path()) {
                if let Err(e) = project.delete(state.config()) {
                    Err(e.into())
                } else {
                    Ok(ClamResponse::NoContent())
                }
            } else {
                Err(ApiError::InvalidName("project name invalid"))
            }
        }
        _ => Err(ApiError::NotAcceptable(
            "Accept header could not be satisfied (try application/json)",
        )),
    }
}

async fn download_file(
    Path(project): Path<String>,
    Path(filename): Path<String>,
    Extension(endpoint_index): Extension<usize>,
    state: State<Arc<ServiceState>>,
    request: Request<Body>,
) -> Result<ClamResponse, ApiError> {
    todo!();
}

async fn upload_file(
    Path(project): Path<String>,
    Path(filename): Path<String>,
    Extension(endpoint_index): Extension<usize>,
    state: State<Arc<ServiceState>>,
    request: Request<Body>,
) -> Result<ClamResponse, ApiError> {
    match negotiate_content_type(request.headers(), &[CONTENT_TYPE_JSON]) {
        Ok(CONTENT_TYPE_JSON) => {
            todo!();
        }
        _ => Err(ApiError::NotAcceptable(
            "Accept header could not be satisfied (try application/json)",
        )),
    }
}

async fn delete_file(
    Path(project): Path<String>,
    Path(filename): Path<String>,
    Extension(endpoint_index): Extension<usize>,
    state: State<Arc<ServiceState>>,
    request: Request<Body>,
) -> Result<ClamResponse, ApiError> {
    match negotiate_content_type(request.headers(), &[CONTENT_TYPE_JSON]) {
        Ok(CONTENT_TYPE_JSON) => {
            todo!();
        }
        _ => Err(ApiError::NotAcceptable(
            "Accept header could not be satisfied (try application/json)",
        )),
    }
}

/// Landing page for the action
async fn get_action(
    state: State<Arc<ServiceState>>,
    Extension(endpoint_index): Extension<usize>,
    request: Request<Body>,
) -> Result<ClamResponse, ApiError> {
    match negotiate_content_type(request.headers(), &[CONTENT_TYPE_JSON, CONTENT_TYPE_HTML]) {
        Ok(CONTENT_TYPE_JSON) => {
            todo!();
        }
        Ok(CONTENT_TYPE_HTML) => {
            todo!();
        }
        _ => Err(ApiError::NotAcceptable(
            "Accept header could not be satisfied (try application/json)",
        )),
    }
}

/// Runs the action
async fn post_action(
    Extension(endpoint_index): Extension<usize>,
    state: State<Arc<ServiceState>>,
    request: Request<Body>,
) -> Result<ClamResponse, ApiError> {
    todo!();
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

fn get_username(headers: &HeaderMap) -> &str {
    //TODO: implement!
    "anonymous"
}

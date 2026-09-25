use crate::ResponseMessage;
use crate::auth::{CurrentUser, auth, callback_handler, login_handler};
use crate::config::{EndPoint, EndPointMode, FileName, ParameterType, ServiceConfig};
use crate::dispatcher::{Dispatcher, Message};
use crate::error::ApiError;
use crate::job::{Job, JobMaster};
use crate::project::{Project, ProjectStatus, project_index};
use crate::state::{ParameterMap, ParameterValue, ServiceState};
use futures_util::StreamExt;
use tokio::fs::File;
use tokio::io::AsyncWriteExt;
use tokio::signal;
use tokio::sync::oneshot;
use tower_http::trace::TraceLayer;
use tracing::{debug, error, info};
use uuid::Uuid;

use axum::Extension;
use axum::Router;
use axum::body::Body;
use axum::extract::{DefaultBodyLimit, Form, FromRequest, Multipart, Path, Query, State};
use axum::http::{HeaderMap, HeaderValue, Request, StatusCode, header};
use axum::middleware::from_fn_with_state;
use axum::response::{IntoResponse, Json, Response};
use axum::routing::{delete, get, post, put};
use serde::Deserialize;
use serde_json::Value;
use std::collections::HashSet;
use std::convert::Infallible;
use std::fs::create_dir_all;
use std::path::PathBuf;
use std::sync::Arc;
use utoipa_swagger_ui::SwaggerUi;

const CONTENT_TYPE_JSON: &str = "application/json";
const CONTENT_TYPE_HTML: &str = "text/html";
const CONTENT_TYPE_PLAINTEXT: &str = "text/plain; charset=UTF-8";

// static resources will be baked into the binary at compile time:
const CSS: &str = include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/static/main.css"));
const JS: &str = include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/static/ui.js"));
const BACKPNG: &[u8] = include_bytes!(concat!(env!("CARGO_MANIFEST_DIR"), "/static/back.png"));

pub struct Service {
    config: ServiceConfig,
}

pub enum ClamResponse {
    Ok(),
    Created(),
    NoContent(),
    Text(String),
    Body {
        stream: Body,
        contenttype: String,
    },
    ProjectResponse(ProjectStatus),
    /// 302 Temporary Redirect
    Redirect(String),
    /// 303 See Other
    RedirectGet(String),
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
            Self::Redirect(url) => (
                StatusCode::TEMPORARY_REDIRECT,
                [
                    cors,
                    server,
                    (
                        header::LOCATION,
                        HeaderValue::try_from(url.as_str()).unwrap(),
                    ),
                ],
            )
                .into_response(),
            Self::RedirectGet(url) => (
                StatusCode::SEE_OTHER,
                [
                    cors,
                    server,
                    (
                        header::LOCATION,
                        HeaderValue::try_from(url.as_str()).unwrap(),
                    ),
                ],
            )
                .into_response(),
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
        let listener = tokio::net::TcpListener::bind(bind)
            .await
            .unwrap_or_else(|e| {
                error!("{}", e);
                std::process::exit(1)
            });
        info!("listening on {}", bind);

        let dispatcher = Dispatcher::new(self.config.clone());
        //launch the dispatcher/job manager as a background thread
        //this is a non-blocking function that spawns the thread and returns immediately
        let state: Arc<ServiceState> = dispatcher.state(); //the dispatcher initiates the state for us
        dispatcher.spawn(); //consumes the dispatcher

        let mut private_routes = Router::new();
        let mut public_routes = Router::new()
            .route("/main.css", get(get_css))
            .route("/ui.js", get(get_js))
            .route("/back.png", get(get_backpng))
            .route("/login", get(login_handler))
            .route("/oidc/callback", get(callback_handler));
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
            .merge(SwaggerUi::new("/info").url("/openapi.json", state.openapi.clone()))
            .route_layer(from_fn_with_state(state.clone(), |state, req, next| {
                auth(state, req, next)
            }))
            .layer(TraceLayer::new_for_http())
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
            EndPointMode::LandingPage => router.route(endpoint.path(), get(get_landingpage)),
            EndPointMode::Project => {
                let sep = if endpoint.path() == "/" { "" } else { "/" };
                let index_path = format!("{}{}projects", endpoint.path(), sep);
                router = router.route(
                    index_path.as_str(),
                    get(get_projects).layer(Extension(endpoint_index)),
                );
                router = router.route(
                    index_path.as_str(),
                    post(post_create_project).layer(Extension(endpoint_index)),
                );
                let path = format!("{}{{project}}", endpoint.path());
                router = router.route(
                    path.as_str(),
                    get(get_project).layer(Extension(endpoint_index)),
                );
                router = router.route(
                    path.as_str(),
                    put(create_project).layer(Extension(endpoint_index)),
                );
                router = router.route(
                    path.as_str(),
                    delete(delete_project).layer(Extension(endpoint_index)),
                );
                router = router.route(
                    path.as_str(),
                    post(submit_project)
                        .layer::<Extension<usize>, Infallible>(Extension(endpoint_index))
                        .layer(DefaultBodyLimit::max(
                            endpoint.max_body_size() * 1024 * 1024,
                        )),
                );

                // Generic file upload endpoint
                let fpath = format!("{}{}{{project}}/upload", endpoint.path(), sep);
                router = router.route(
                    fpath.as_str(),
                    get(upload_input_file_multipart)
                        .layer::<Extension<usize>, Infallible>(Extension(endpoint_index))
                        .layer(DefaultBodyLimit::max(
                            endpoint.max_body_size() * 1024 * 1024,
                        )),
                );

                // File output endpoints
                let fpath = format!("{}{}{{project}}/output/{{filename}}", endpoint.path(), sep);
                router = router.route(
                    fpath.as_str(),
                    get(download_output_file).layer(Extension(endpoint_index)),
                );

                //File uploading/download/deletion endpoints within a project
                let fpath = format!(
                    "{}{}{{project}}/{{parameter_id}}/{{filename}}",
                    endpoint.path(),
                    sep
                );
                router = router.route(
                    fpath.as_str(),
                    get(download_input_file).layer(Extension(endpoint_index)),
                );
                router = router.route(
                    fpath.as_str(),
                    put(upload_input_file)
                        .layer::<Extension<usize>, Infallible>(Extension(endpoint_index))
                        .layer(DefaultBodyLimit::max(
                            endpoint.max_body_size() * 1024 * 1024,
                        )),
                );
                router = router.route(
                    fpath.as_str(),
                    delete(delete_input_file).layer(Extension(endpoint_index)),
                );

                router
            }
            EndPointMode::Action => {
                // Both GET or POST are fine for actions
                router = router.route(
                    endpoint.path(),
                    get(get_action).layer(Extension(endpoint_index)),
                );
                router = router.route(
                    endpoint.path(),
                    post(post_action)
                        .layer::<Extension<usize>, Infallible>(Extension(endpoint_index))
                        .layer(DefaultBodyLimit::max(
                            endpoint.max_body_size() * 1024 * 1024,
                        )),
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
        Err(e) => Err(ApiError::InternalError(format!(
            "Internal error whilst serializing OpenAPI specification to JSON: {}",
            e
        ))),
    }
}

async fn get_css() -> Result<ClamResponse, ApiError> {
    Ok(ClamResponse::Body {
        stream: CSS.into(),
        contenttype: "text/css".into(),
    })
}

async fn get_js() -> Result<ClamResponse, ApiError> {
    Ok(ClamResponse::Body {
        stream: JS.into(),
        contenttype: "text/javascript".into(),
    })
}

async fn get_backpng() -> Result<ClamResponse, ApiError> {
    Ok(ClamResponse::Body {
        stream: BACKPNG.into(),
        contenttype: "image/png".into(),
    })
}

async fn get_landingpage(
    state: State<Arc<ServiceState>>,
    request: Request<Body>,
) -> Result<ClamResponse, ApiError> {
    match negotiate_content_type(request.headers(), &[CONTENT_TYPE_HTML, CONTENT_TYPE_JSON]) {
        Ok(CONTENT_TYPE_JSON) => get_api(state).await,
        Ok(CONTENT_TYPE_HTML) if !state.config().disable_ui() => {
            state.render_template("landingpage", "text/html; charset=utf-8", None)
        }
        _ => Err(ApiError::NotAcceptable(
            "Accept header could not be satisfied (try application/json)",
        )),
    }
}

/// Presents a list of projects for a given user and endpoint
async fn get_projects(
    Extension(endpoint_index): Extension<usize>,
    Extension(user): Extension<CurrentUser>,
    state: State<Arc<ServiceState>>,
    request: Request<Body>,
) -> Result<ClamResponse, ApiError> {
    let endpoint = state.endpoint(endpoint_index);
    match negotiate_content_type(request.headers(), &[CONTENT_TYPE_HTML, CONTENT_TYPE_JSON]) {
        Ok(CONTENT_TYPE_JSON) => match project_index(user.as_str(), endpoint, state.config()) {
            Ok(projects) => Ok(ClamResponse::JsonList(
                projects.into_iter().map(|project| project.into()).collect(),
            )),
            Err(e) => Err(ApiError::InternalError(format!(
                "Unable to obtain project list: {}",
                e
            ))),
        },
        Ok(CONTENT_TYPE_HTML) => match project_index(user.as_str(), endpoint, state.config()) {
            Ok(projects) => state.render_template(
                "projectindex",
                "text/html; charset=utf-8",
                Some(upon::value! {
                    name: endpoint.name().clone().unwrap_or_default(),
                    description: endpoint.description().clone().unwrap_or_default(),
                    path: endpoint.path(),
                    projects: projects.into_iter().map(|project| project.into()).collect::<Vec<String>>(),
                }),
            ),
            Err(e) => Err(ApiError::InternalError(format!(
                "Unable to obtain project list: {}",
                e
            ))),
        },
        _ => Err(ApiError::NotAcceptable(
            "Accept header could not be satisfied (try application/json)",
        )),
    }
}

async fn get_project(
    Path(project): Path<String>,
    Extension(endpoint_index): Extension<usize>,
    Extension(user): Extension<CurrentUser>,
    state: State<Arc<ServiceState>>,
    request: Request<Body>,
) -> Result<ClamResponse, ApiError> {
    if let Ok(project) = Project::new(project, user.as_str(), endpoint_index, state.config()) {
        match negotiate_content_type(request.headers(), &[CONTENT_TYPE_JSON, CONTENT_TYPE_HTML]) {
            Ok(CONTENT_TYPE_JSON) => {
                if let Some(projectstatus) = state.project_status(&project) {
                    Ok(ClamResponse::ProjectResponse(projectstatus))
                } else {
                    debug!("project not found: {}", project.name());
                    Err(ApiError::NotFound("No such project".into()))
                }
            }
            Ok(CONTENT_TYPE_HTML) if !state.config().disable_ui() => {
                if let Some(projectstatus) = state.project_status(&project) {
                    state.render_template(
                        "project",
                        "text/html; charset=utf-8",
                        Some(upon::value! {
                            name: project.endpoint().name().clone().unwrap_or_default(),
                            description: project.endpoint().description().clone().unwrap_or_default(),
                            parentpath: format!("{}{}", project.endpoint().path(), "projects"),
                            project: project.name(),
                            path: format!("{}{}", project.endpoint().path(), project.name()),
                            status: projectstatus,
                            parameters: project.endpoint().parameters(),
                        }),
                    )
                } else {
                    debug!("project not found: {}", project.name());
                    Err(ApiError::NotFound("No such project".into()))
                }
            }
            _ => Err(ApiError::NotAcceptable(
                "Accept header could not be satisfied (try application/json)",
            )),
        }
    } else {
        debug!("project name invalid");
        Err(ApiError::InvalidName("project name invalid"))
    }
}

async fn submit_project(
    Path(project): Path<String>,
    Extension(endpoint_index): Extension<usize>,
    Extension(user): Extension<CurrentUser>,
    state: State<Arc<ServiceState>>,
    mut param_map: ParameterMap,
) -> Result<ClamResponse, ApiError> {
    if let Ok(project) = Project::new(project, user.as_str(), endpoint_index, state.config()) {
        param_map.finish_uploads(state.endpoint(endpoint_index), &project)?;
        debug!("Received project parameters: {:?}", param_map);
        let job = Job::new(
            &state,
            JobMaster::EndPoint(endpoint_index),
            Some(&project),
            state.endpoint(endpoint_index).background_services(),
            &user,
            param_map,
        );
        if let Some(error) = job.error {
            return Err(ApiError::ParameterError(error));
        }
        //ensure necessary background services are scheduled or already running
        for bgservice in job.background_services().iter() {
            state.schedule_background_service(*bgservice).await?
        }
        let (tx, rx) = oneshot::channel();
        state.send(Message::SubmitJob(job, tx));
        match rx.await {
            Ok(ResponseMessage::JobSubmitted) => Ok(ClamResponse::RedirectGet(format!(
                "{}{}",
                state.config().url().as_deref().unwrap_or_default(),
                project.endpoint().path(),
            ))),
            Ok(ResponseMessage::JobError(error)) => Err(ApiError::ServiceUnavailable(error)),
            Err(e) => Err(ApiError::InternalError(format!(
                "oneshot sender dropped whilst submitting a job: {}",
                e
            ))),
            Ok(m) => Err(ApiError::InternalError(format!(
                "unexpected response message whilst submitting a job: {:?}",
                m
            ))),
        }
    } else {
        Err(ApiError::NotFound("No such project".into()))
    }
}

async fn create_project(
    Path(project): Path<String>,
    Extension(endpoint_index): Extension<usize>,
    Extension(user): Extension<CurrentUser>,
    state: State<Arc<ServiceState>>,
) -> Result<ClamResponse, ApiError> {
    if let Ok(project) = Project::new(project, user.as_str(), endpoint_index, state.config()) {
        if let Err(e) = project.create() {
            Err(e.into())
        } else {
            Ok(ClamResponse::Created())
        }
    } else {
        Err(ApiError::InvalidName("project name invalid"))
    }
}

#[derive(Deserialize)]
struct CreateForm {
    project: String,
}

/// Alternative endpoint for project creation using POST request on index
async fn post_create_project(
    Extension(endpoint_index): Extension<usize>,
    Extension(user): Extension<CurrentUser>,
    state: State<Arc<ServiceState>>,
    form: Form<CreateForm>,
) -> Result<ClamResponse, ApiError> {
    if let Ok(project) = Project::new(&form.project, user.as_str(), endpoint_index, state.config())
    {
        if let Err(e) = project.create() {
            Err(e.into())
        } else {
            Ok(ClamResponse::RedirectGet(project.url()))
        }
    } else {
        Err(ApiError::InvalidName("project name invalid"))
    }
}

async fn delete_project(
    Path(project): Path<String>,
    Extension(endpoint_index): Extension<usize>,
    Extension(user): Extension<CurrentUser>,
    state: State<Arc<ServiceState>>,
) -> Result<ClamResponse, ApiError> {
    if let Ok(project) = Project::new(project, user.as_str(), endpoint_index, state.config()) {
        if let Ok(mut project_job_map) = state.project_job_map.write() {
            project_job_map.remove(&project.key());
            //kill all remaining associated job if any
            if let Some(job_id) = project_job_map.get(project.key()) {
                if let Ok(running_jobs) = state.running_jobs.read() {
                    if let Some(job) = running_jobs.get(job_id) {
                        job.kill();
                        job.wait(); //wait until job is gone
                    }
                }
            }
        }
        if let Err(e) = project.delete() {
            Err(e.into())
        } else {
            Ok(ClamResponse::NoContent())
        }
    } else {
        Err(ApiError::InvalidName("project name invalid"))
    }
}

async fn download_output_file(
    Path((project, filename)): Path<(String, String)>,
    Extension(endpoint_index): Extension<usize>,
    Extension(user): Extension<CurrentUser>,
    state: State<Arc<ServiceState>>,
) -> Result<ClamResponse, ApiError> {
    if let Ok(project) = Project::new(project, user.as_str(), endpoint_index, state.config()) {
        //download output file without keeping it all in memory
        if let Some(filepath) = project.output_file(filename.as_str()) {
            let stream: axum::body::Body = project.file_body(&filepath).await?;
            let contenttype = if let Some(filetype) = project.output_filetype(filename.as_str()) {
                filetype.contenttype().to_string()
            } else {
                "application/octet-stream".to_string()
            };
            Ok(ClamResponse::Body {
                stream,
                contenttype,
            })
        } else {
            Err(ApiError::NotFound("Output file not found".into()))
        }
    } else {
        Err(ApiError::InvalidName("project name invalid"))
    }
}

async fn download_input_file(
    Path((project, parameter_id, filename)): Path<(String, String, String)>,
    Extension(endpoint_index): Extension<usize>,
    Extension(user): Extension<CurrentUser>,
    state: State<Arc<ServiceState>>,
) -> Result<ClamResponse, ApiError> {
    if state.config().disable_input_download() {
        return Err(ApiError::PermissionDenied(
            "Input file download is disabled".into(),
        ));
    }
    if let Ok(project) = Project::new(project, user.as_str(), endpoint_index, state.config()) {
        let parameter = project
            .endpoint()
            .parameter(parameter_id.as_str())
            .ok_or_else(|| ApiError::InvalidName("Invalid parameter specified for download"))?;
        //download input file without keeping it all in memory
        if let Some(filepath) = project.input_file(parameter_id.as_str(), filename.as_str(), true) {
            let stream: axum::body::Body = project.file_body(&filepath).await?;
            let contenttype = if let Some(filetype) = parameter.filetype(state.config()) {
                filetype.contenttype().to_string()
            } else {
                "application/octet-stream".to_string()
            };
            Ok(ClamResponse::Body {
                stream,
                contenttype,
            })
        } else {
            Err(ApiError::NotFound("Input file not found".into()))
        }
    } else {
        Err(ApiError::InvalidName("project name invalid"))
    }
}

async fn upload_input_file(
    Path((project, parameter_id, filename)): Path<(String, String, String)>,
    Extension(endpoint_index): Extension<usize>,
    Extension(user): Extension<CurrentUser>,
    state: State<Arc<ServiceState>>,
    request: Request<Body>,
) -> Result<ClamResponse, ApiError> {
    if let Ok(project) = Project::new(project, user.as_str(), endpoint_index, state.config()) {
        debug!(
            "upload_input_file: project={}, parameter_id={}, filename={}",
            project.name(),
            parameter_id,
            filename
        );
        let parameter = project
            .endpoint()
            .parameter(parameter_id.as_str())
            .ok_or_else(|| ApiError::InvalidName("Invalid parameter specified for upload"))?;
        let filename = parameter.validate_filename(filename.as_str())?;
        //upload input file without keeping it all in memory
        if let Some(filepath) = project.input_file(parameter_id.as_str(), filename.as_str(), false)
        {
            //MAYBE TODO: Check for matching content-type? We just accept anything as-is right now
            let mut body_stream = request.into_body().into_data_stream();
            project.create_parameter_dir(parameter_id.as_str())?;
            let mut file = File::create(&filepath)
                .await
                .map_err(|e| ApiError::InternalError(format!("Failed to create file: {}", e)))?;

            // Stream chunks directly from the network to the disk
            while let Some(chunk_result) = body_stream.next().await {
                let chunk = chunk_result.map_err(|e| {
                    ApiError::UploadError(format!("Network error while streaming: {e}"))
                })?;
                file.write_all(&chunk).await.map_err(|e| {
                    ApiError::InternalError(format!("Failed to write uploaded chunk: {e}"))
                })?;
            }

            file.flush().await.map_err(|e| {
                ApiError::InternalError(format!("Failed to flush after upload: {e}"))
            })?;

            Ok(ClamResponse::Created())
        } else {
            //should be unreachable, but just to be sure:
            Err(ApiError::InternalError(
                "upload_input_file, couldn't get input file (this should not happen)".into(),
            ))
        }
    } else {
        Err(ApiError::InvalidName("project name invalid"))
    }
}

async fn upload_input_file_multipart(
    Path((project, parameter_id)): Path<(String, String)>,
    Extension(endpoint_index): Extension<usize>,
    Extension(user): Extension<CurrentUser>,
    state: State<Arc<ServiceState>>,
    mut multipart: Multipart,
) -> Result<ClamResponse, ApiError> {
    let project = Project::new(project, user.as_str(), endpoint_index, state.config())
        .map_err(|_| ApiError::InvalidName("project name invalid"))?;

    let parameter = project
        .endpoint()
        .parameter(parameter_id.as_str())
        .ok_or_else(|| ApiError::InvalidName("Invalid parameter specified for upload"))?;

    // Iterate through all the fields/files in the multipart form submission
    while let Some(mut field) = multipart
        .next_field()
        .await
        .map_err(|e| ApiError::UploadError(format!("Upload error in Multipart: {e}")))?
    {
        let filename = parameter.validate_filename(field.name().unwrap_or_default())?;

        if let Some(filepath) = project.input_file(parameter_id.as_str(), filename.as_str(), false)
        {
            project.create_parameter_dir(parameter_id.as_str())?;
            let mut file = File::create(&filepath)
                .await
                .map_err(|e| ApiError::InternalError(format!("Failed to create file: {e}")))?;

            while let Some(chunk_result) = field.next().await {
                let chunk = chunk_result.map_err(|e| {
                    ApiError::UploadError(format!("Error reading multipart upload chunk: {e}"))
                })?;

                file.write_all(&chunk).await.map_err(|e| {
                    ApiError::InternalError(format!("File upload write error: {e}"))
                })?;
            }

            file.flush().await.map_err(|e| {
                ApiError::InternalError(format!("Flush error after file upload: {e}"))
            })?;
        } else {
            return Err(ApiError::NotFound(
                "Input file path generation failed".into(),
            ));
        }
    }

    Ok(ClamResponse::Created())
}

async fn delete_input_file(
    Path((project, parameter_id, filename)): Path<(String, String, String)>,
    Extension(endpoint_index): Extension<usize>,
    Extension(user): Extension<CurrentUser>,
    state: State<Arc<ServiceState>>,
) -> Result<ClamResponse, ApiError> {
    if let Ok(project) = Project::new(project, user.as_str(), endpoint_index, state.config()) {
        project
            .endpoint()
            .parameter(parameter_id.as_str())
            .ok_or_else(|| ApiError::InvalidName("Invalid parameter specified for upload"))?;

        //delete input file
        if let Some(filepath) = project.input_file(parameter_id.as_str(), filename.as_str(), true) {
            std::fs::remove_file(filepath)?;
            Ok(ClamResponse::NoContent())
        } else {
            Err(ApiError::NotFound("Input file not found".into()))
        }
    } else {
        Err(ApiError::InvalidName("project name invalid"))
    }
}

/// Runs the action (Helper function called by get_action or post_action)
async fn run_action(
    state: State<Arc<ServiceState>>,
    endpoint_index: usize,
    user: &CurrentUser,
    query: ParameterMap,
    contenttype: String,
) -> Result<ClamResponse, ApiError> {
    let job = Job::new(
        &state,
        JobMaster::EndPoint(endpoint_index),
        None,
        state.endpoint(endpoint_index).background_services(),
        user,
        query,
    );
    if let Some(error) = job.error {
        return Err(ApiError::ParameterError(error));
    }
    let (tx, rx) = oneshot::channel();
    debug!("run_action: submitting job {:?}", job);
    //ensure necessary background services are scheduled or already running
    for bgservice in job.background_services().iter() {
        state.schedule_background_service(*bgservice).await?
    }
    let job_id = *job.id();
    state.send(Message::SubmitJob(job, tx));
    //MAYBE TODO: use a gradually increasing poll interval or refactor messaging system to remove this latency altogether
    let poll_interval = tokio::time::Duration::new(0, 50000000); //50ms
    match rx.await {
        Ok(ResponseMessage::JobSubmitted) => {
            debug!("run_action: job {} submitted", job_id);
            //now poll for the job
            loop {
                let (tx, rx) = oneshot::channel();
                state.send(Message::PollJob(job_id, tx));
                match rx.await {
                    Ok(ResponseMessage::JobFinished {
                        id,
                        exitstatus,
                        output,
                        error,
                    }) => {
                        debug!(
                            "run_action: job {} finished with status {:?}",
                            id, exitstatus
                        );
                        match exitstatus {
                            0 => {
                                return Ok(ClamResponse::Body {
                                    stream: output.into(),
                                    contenttype,
                                });
                            }
                            40 => return Err(ApiError::ParameterError(error)),
                            44 => return Err(ApiError::NotFound(error)),
                            43 => return Err(ApiError::PermissionDenied(error)),
                            _ => {
                                return Err(ApiError::InternalError(format!(
                                    "An error occurred during execution of this action (exitcode {}):\n\n{}",
                                    exitstatus, error
                                )));
                            }
                        }
                    }
                    Ok(ResponseMessage::JobRunning(..)) | Ok(ResponseMessage::JobPending) => {
                        tokio::time::sleep(poll_interval).await
                    }
                    Ok(ResponseMessage::JobError(error)) => {
                        debug!("run_action: job error: {}", error);
                        return Err(ApiError::InternalError(error));
                    }
                    Err(e) => {
                        return Err(ApiError::InternalError(format!(
                            "oneshot sender dropped whilst polling a job: {}",
                            e
                        )));
                    }
                    Ok(m) => {
                        return Err(ApiError::InternalError(format!(
                            "unexpected response message whilst polling a job: {:?}",
                            m
                        )));
                    }
                }
            }
        }
        Ok(ResponseMessage::JobError(error)) => {
            debug!("run_action: job failed");
            Err(ApiError::ServiceUnavailable(error))
        }
        Err(e) => Err(ApiError::InternalError(format!(
            "oneshot sender dropped whilst submitting a job: {}",
            e
        ))),
        Ok(m) => Err(ApiError::InternalError(format!(
            "unexpected response message whilst submitting a job: {:?}",
            m
        ))),
    }
}

/// Landing page for the action (if text/html is requested), if the output content-type is requested (and the necessary parameters are supplied) it will run the action
async fn get_action(
    state: State<Arc<ServiceState>>,
    Extension(endpoint_index): Extension<usize>,
    Extension(user): Extension<CurrentUser>,
    headers: HeaderMap<HeaderValue>,
    query: Query<Vec<(String, String)>>,
) -> Result<ClamResponse, ApiError> {
    let endpoint = state.endpoint(endpoint_index);
    let mut accepted_data = vec![CONTENT_TYPE_HTML];
    if let Some(filetype) = endpoint.filetype() {
        if let Some(filetype) = state.config().filetype(filetype) {
            let contenttype = filetype.contenttype().as_str();
            if contenttype != "text/html" {
                accepted_data.push(contenttype);
            }
        }
    }
    match negotiate_content_type(&headers, &accepted_data) {
        Ok(CONTENT_TYPE_HTML) if !state.config().disable_ui() => state.render_template(
            "action",
            "text/html; charset=utf-8",
            Some(upon::value! {
                name: endpoint.name().clone().unwrap_or_default(),
                description: endpoint.description().clone().unwrap_or_default(),
                path: endpoint.path(),
                parameters: endpoint.parameters(),
            }),
        ),
        Ok(filetype) => {
            let filetype = filetype.to_string();
            run_action(
                state,
                endpoint_index,
                &user,
                ParameterMap(
                    query
                        .0
                        .into_iter()
                        .map(|(k, v)| (k, Into::<ParameterValue>::into(v)))
                        .collect(),
                ), //MAYBE TODO: work away extra allocation?
                filetype,
            )
            .await
        }
        _ => Err(ApiError::NotAcceptable(
            "Accept header could not be satisfied (try a POST request instead if you don't know what to expect)",
        )),
    }
}

/// Runs the action.
async fn post_action(
    Extension(endpoint_index): Extension<usize>,
    Extension(user): Extension<CurrentUser>,
    state: State<Arc<ServiceState>>,
    param_map: ParameterMap,
) -> Result<ClamResponse, ApiError> {
    //we ignore Accept headers for POST and just deliver what the action provides
    let mut contenttype = CONTENT_TYPE_PLAINTEXT;
    let endpoint = state.endpoint(endpoint_index);
    if let Some(filetype) = endpoint.filetype() {
        if let Some(filetype) = state.config().filetype(filetype) {
            contenttype = filetype.contenttype().as_str();
        }
    }
    let contenttype: String = contenttype.into();
    run_action(state, endpoint_index, &user, param_map, contenttype).await
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

    tokio::select! {
        _ = ctrl_c => {
            info!("SIGINT received, waiting for jobs to end..");
            wait_shutdown(state).await;
            info!("Bye bye!");
            std::process::exit(0);
        }
        _ = terminate => {
            info!("SIGTERM received, waiting for jobs to end..");
            wait_shutdown(state).await;
            info!("Bye bye!");
            std::process::exit(0);
        }
    }
}

async fn wait_shutdown(state: Arc<ServiceState>) {
    let mut have_running_jobs = true;
    let mut signaled: HashSet<usize> = HashSet::new();
    if let Ok(mut pending_jobs) = state.pending_jobs.write() {
        pending_jobs.clear();
    }
    while have_running_jobs {
        if let Ok(running_jobs) = state.running_jobs.read() {
            have_running_jobs = false;
            for (job_id, _) in running_jobs.iter() {
                have_running_jobs = true;
                if !signaled.contains(job_id) {
                    signaled.insert(*job_id);
                    state.send(Message::CancelJob(*job_id, None));
                }
            }
        }
        if have_running_jobs {
            tokio::time::sleep(std::time::Duration::from_millis(100)).await
        }
    }
}

impl<S> FromRequest<S> for ParameterMap
where
    S: Send + Sync,
{
    type Rejection = Response;

    async fn from_request(request: Request<Body>, state: &S) -> Result<Self, Self::Rejection> {
        let is_multipart = request
            .headers()
            .get(axum::http::header::CONTENT_TYPE)
            .and_then(|value| value.to_str().ok())
            .is_some_and(|value| value.starts_with("multipart/form-data"));

        let is_form = request
            .headers()
            .get(axum::http::header::CONTENT_TYPE)
            .and_then(|value| value.to_str().ok())
            .is_some_and(|value| value.starts_with("application/x-www-form-urlencoded"));

        if is_multipart {
            let multipart = Multipart::from_request(request, state)
                .await
                .map_err(IntoResponse::into_response)?;
            Ok(Self::from_multipart(multipart).await)
        } else if is_form {
            Form::<Vec<(String, String)>>::from_request(request, state)
                .await
                .map(|Form(value)| {
                    ParameterMap(value.into_iter().map(|x| (x.0, x.1.into())).collect())
                })
                .map_err(IntoResponse::into_response)
        } else {
            let (_, body) = request.into_parts();
            let body = axum::body::to_bytes(body, usize::MAX)
                .await
                .map_err(|error| {
                    (
                        StatusCode::BAD_REQUEST,
                        format!("failed to read request body: {error}"),
                    )
                        .into_response()
                })?;

            if body.is_empty() {
                //empty body -> empty map, this is an allowed scenario
                Ok(ParameterMap::new())
            } else {
                Err((
                    StatusCode::UNSUPPORTED_MEDIA_TYPE,
                    "Request body must be multipart/form-data or application/x-www-form-urlencoded",
                )
                    .into_response())
            }
        }
    }
}

impl ParameterMap {
    /// loads all parameters from Multipart request body into memory (and files immediately to disk)
    async fn from_multipart(mut multipart: Multipart) -> Self {
        debug!("from_multipart: Processing multipart body...");
        let mut param_map = Vec::new();
        while let Some(mut field) = multipart
            .next_field()
            .await
            .expect("unable to extract field from multipart")
        {
            if let Some(filename) = field.file_name() {
                let filename = filename.to_string();
                // put file in a temporary upload area so it's not kept in memory
                // at this point we don't know the project path yet
                // the final move will be done later by `finish_upload()`
                let tmpid = Uuid::new_v4();
                let mut tmpfilepath: PathBuf = "./data/tmpupload/".into();
                create_dir_all(&tmpfilepath).expect("Failed to create tmpupload directory");
                tmpfilepath.push(format!("{}", tmpid));

                let mut file = File::create(&tmpfilepath)
                    .await
                    .expect("Failed to upload file into temporary upload");

                // Stream chunks directly from the network to the disk
                while let Ok(Some(chunk_result)) = field.chunk().await {
                    file.write_all(&chunk_result)
                        .await
                        .expect("Failed to write uploaded chunk");
                }

                debug!(
                    "from_multipart: Uploaded {} for parameter {} to temporary storage as {:?}",
                    filename,
                    field.name().unwrap_or_default(),
                    tmpfilepath
                );
                param_map.push((
                    field.name().expect("field must have a name").to_string(),
                    ParameterValue::File {
                        filename,
                        contents: String::new(),
                        tmpfilepath: Some(tmpfilepath),
                    },
                ));
            } else {
                param_map.push((
                    field.name().expect("field must have a name").to_string(),
                    field
                        .text()
                        .await
                        .expect("unable to extract value from multipart")
                        .into(),
                ));
            }
        }
        ParameterMap(param_map)
    }

    pub(crate) fn get(&self, parameter_id: &str) -> Option<&ParameterValue> {
        self.iter()
            .find_map(|(k, v)| if k == parameter_id { Some(v) } else { None })
    }

    /// Moves uploaded files from the temporary upload to the project path, validating the filenames in the process. Returns true if all input files are accepted
    pub(crate) fn finish_uploads(
        &mut self,
        endpoint: &EndPoint,
        project: &Project,
    ) -> Result<(), ApiError> {
        let mut err = None;
        for (parameter_id, value) in self.0.iter_mut() {
            if let ParameterValue::File {
                filename,
                tmpfilepath,
                ..
            } = value
            {
                if let Some(parameter) = endpoint.parameter(parameter_id) {
                    if let ParameterType::File {
                        filename: reffilename,
                        ..
                    } = parameter.r#type()
                    {
                        //validate filename
                        let filename = if let FileName::Exact(reffilename) = reffilename {
                            //server coerces an exact filename, we don't care what the client provided and override it
                            reffilename.as_str()
                        } else if let FileName::Pattern(pattern) = reffilename {
                            //client filename must match pattern
                            if !pattern.is_match(filename.as_str()) && err.is_none() {
                                err = Some(ApiError::ParameterError(format!(
                                    "parameter {}: provided filename {} did not match pattern {}",
                                    parameter.id(),
                                    filename,
                                    pattern
                                )));
                            }
                            filename.as_str()
                        } else {
                            filename.as_str()
                        };

                        //move file from temporary upload to final destination in project
                        if let Some(tmpfilepath) = tmpfilepath.take() {
                            if err.is_none() {
                                project.create_parameter_dir(parameter_id)?;
                            }
                            if err.is_some() {
                                std::fs::remove_file(tmpfilepath)?;
                            } else if let Some(filepath) =
                                project.input_file(parameter_id.as_str(), filename, false)
                            {
                                if let Err(e) = std::fs::rename(tmpfilepath, filepath) {
                                    err = Some(ApiError::InternalError(format!(
                                        "Failed to finish upload for parameter {}, file {}: {}",
                                        parameter.id(),
                                        filename,
                                        e
                                    )));
                                }
                            } else {
                                //or if input is not accepted for any other reason, delete it
                                // MAYBE TODO: I don't think this can happen
                                std::fs::remove_file(tmpfilepath)?;
                                err = Some(ApiError::InternalError(format!(
                                    "file input not accepted for parameter {}",
                                    parameter.id(),
                                )));
                            }
                        }
                    } else {
                        unreachable!("parameter type must be file");
                    }
                }
            }
        }
        if let Some(err) = err {
            Err(err) //in case of multiple errors, only the first one is returned, but proper cleanup is done for all
        } else {
            Ok(())
        }
    }
}

fn negotiate_content_type<'a>(
    headers: &HeaderMap<HeaderValue>,
    offer_types: &[&'a str],
) -> Result<&'a str, ApiError> {
    if let Some(accept_types) = headers.get(axum::http::header::ACCEPT) {
        let mut match_accept_index = None;
        let mut matching_offer = None;
        for (i, accept_type) in accept_types
            .to_str()
            .map_err(|_| ApiError::NotAcceptable("Invalid Accept header"))
            .unwrap_or(CONTENT_TYPE_JSON) //if we get no accept header we assume we're dealing with a lazy automated client and serve JSON
            .split(",")
            .enumerate()
        {
            let accept_type = accept_type.split(";").next().unwrap();
            for offer_type in offer_types.iter() {
                let offer_type = offer_type.split(";").next().unwrap();
                if offer_type == accept_type
                    || accept_type == "*/*"
                        && (match_accept_index.is_none()
                            || (match_accept_index.is_some() && match_accept_index.unwrap() > i))
                {
                    match_accept_index = Some(i);
                    matching_offer = Some(offer_type);
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

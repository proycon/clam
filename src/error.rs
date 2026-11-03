use crate::service::ClamResponse;
use crate::state::ServiceState;
use axum::{
    http::StatusCode,
    response::{IntoResponse, Json, Response},
};
use serde::Serialize;
use serde::ser::SerializeStruct;

#[derive(Debug)]
pub enum ClamError {
    MissingEnvVariable(String),
    ConfigError(toml::de::Error),
    ConfigValidationError(String),
    IoError(std::io::Error),
}

#[derive(Debug)]
pub enum ApiError {
    InternalError(String),
    /// client-side upload error (HTTP 400)
    UploadError(String),
    NotFound(String),
    NotAcceptable(&'static str),
    PermissionDenied(String),
    ParameterError(String),
    InvalidName(&'static str),
    ServiceUnavailable(String),
    TemplateError(upon::Error),
}

impl Serialize for ApiError {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        let mut state = serializer.serialize_struct("ApiError", 2)?;
        match self {
            Self::NotFound(s) => {
                state.serialize_field("type", "NotFound")?;
                state.serialize_field("message", s)?;
            }
            Self::NotAcceptable(s) => {
                state.serialize_field("type", "NotAcceptable")?;
                state.serialize_field("message", s)?;
            }
            Self::PermissionDenied(s) => {
                state.serialize_field("type", "PermissionDenied")?;
                state.serialize_field("message", s)?;
            }
            Self::ParameterError(s) => {
                state.serialize_field("type", "ParameterError")?;
                state.serialize_field("message", s)?;
            }
            Self::UploadError(s) => {
                state.serialize_field("type", "UploadError")?;
                state.serialize_field("message", s)?;
            }
            Self::InternalError(s) => {
                state.serialize_field("type", "InternalError")?;
                state.serialize_field("message", s)?;
            }
            Self::TemplateError(e) => {
                state.serialize_field("type", "TemplateError")?;
                state.serialize_field("message", &format!("{}", e))?;
            }
            Self::ServiceUnavailable(s) => {
                state.serialize_field("type", "ServiceUnavailable")?;
                state.serialize_field("message", s)?;
            }
            Self::InvalidName(s) => {
                state.serialize_field("type", "InvalidName")?;
                state.serialize_field("message", s)?;
            }
        }
        state.end()
    }
}

impl ApiError {
    pub fn statuscode(&self) -> StatusCode {
        match self {
            Self::InternalError(..) | Self::TemplateError(..) => StatusCode::INTERNAL_SERVER_ERROR,
            Self::PermissionDenied(..) => StatusCode::FORBIDDEN,
            Self::ServiceUnavailable(..) => StatusCode::SERVICE_UNAVAILABLE,
            Self::NotAcceptable(..) => StatusCode::NOT_ACCEPTABLE,
            Self::ParameterError(..) | Self::InvalidName(..) | Self::UploadError(..) => {
                StatusCode::BAD_REQUEST
            }
            _ => StatusCode::NOT_FOUND,
        }
    }

    pub fn into_json_response(self) -> Response {
        (self.statuscode(), Json(self)).into_response()
    }

    pub fn into_html_response(self, state: &ServiceState) -> Response {
        let statuscode = self.statuscode();
        let statuscode_int = statuscode.as_u16();
        let context = match self {
            Self::NotFound(s) => {
                upon::value! {
                    statuscode: statuscode_int,
                    title: "Not Found",
                    message: s,
                }
            }
            Self::NotAcceptable(s) => {
                upon::value! {
                    statuscode: statuscode_int,
                    title: "Not Acceptable",
                    message: s,
                }
            }
            Self::PermissionDenied(s) => {
                upon::value! {
                    statuscode: statuscode_int,
                    title: "Permission Denied",
                    message: s,
                }
            }
            Self::ParameterError(s) => {
                upon::value! {
                    statuscode: statuscode_int,
                    title: "Parameter Error",
                    message: s,
                }
            }
            Self::UploadError(s) => {
                upon::value! {
                    statuscode: statuscode_int,
                    title: "Upload Error",
                    message: s,
                }
            }
            Self::InternalError(s) => {
                upon::value! {
                    statuscode: statuscode_int,
                    title: "Internal Error",
                    message: s,
                }
            }
            Self::TemplateError(s) => {
                upon::value! {
                    statuscode: statuscode_int,
                    title: "Template Error",
                    message: format!("{}", s),
                }
            }
            Self::ServiceUnavailable(s) => {
                upon::value! {
                    statuscode: statuscode_int,
                    title: "Service Unavailable",
                    message: s,
                }
            }
            Self::InvalidName(s) => {
                upon::value! {
                    statuscode: statuscode_int,
                    title: "Service Unavailable",
                    message: s,
                }
            }
        };
        match state.render_template("error", "text/html; charset=utf-8", Some(context)) {
            Ok(ClamResponse::Text(s)) => (statuscode, s).into_response(),
            Ok(ClamResponse::Body {
                stream,
                contenttype: _,
            }) => (statuscode, stream).into_response(),
            Ok(_) => unreachable!("Unexpected ClamResponse in ApiError::into_html_response()"),
            Err(s) => s.into_json_response(), //if the templating system returns an error at this point it will be returned as JSON instead of HTML (to prevent recursive loops)
        }
    }
}

/*
impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        self.into_json_response()
    }
}
*/

/*
impl From<ClamError> for ApiError {
    fn from(value: ClamError) -> Self {
    }
}
*/

impl From<std::io::Error> for ApiError {
    fn from(value: std::io::Error) -> Self {
        match value.kind() {
            std::io::ErrorKind::NotFound => Self::NotFound("file not found on filesystem".into()),
            std::io::ErrorKind::PermissionDenied => {
                Self::PermissionDenied("permission denied on filesystem".into())
            }
            std::io::ErrorKind::NotSeekable => {
                Self::InternalError(format!("file not seekable: {}", value))
            }
            std::io::ErrorKind::StorageFull => {
                Self::InternalError(format!("storage full: {}", value))
            }
            std::io::ErrorKind::ReadOnlyFilesystem => {
                Self::InternalError(format!("read only filesystem: {}", value))
            }
            _ => Self::InternalError(format!("File I/O error: {}", value)),
        }
    }
}

impl From<axum::Error> for ApiError {
    fn from(value: axum::Error) -> Self {
        Self::InternalError(format!("web framework error: {}", value))
    }
}

impl From<upon::Error> for ApiError {
    fn from(value: upon::Error) -> Self {
        Self::TemplateError(value)
    }
}

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
    IoError(std::io::Error),
}

#[derive(Debug)]
pub enum ApiError {
    InternalError(&'static str),
    NotFound(&'static str),
    NotAcceptable(&'static str),
    PermissionDenied(&'static str),
    ParameterError(&'static str),
    InvalidName(&'static str),
    ServiceUnavailable(String),
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
            Self::InternalError(s) => {
                state.serialize_field("type", "InternalError")?;
                state.serialize_field("message", s)?;
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

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        let statuscode = match self {
            Self::InternalError(..) => StatusCode::INTERNAL_SERVER_ERROR,
            Self::PermissionDenied(..) => StatusCode::FORBIDDEN,
            Self::ServiceUnavailable(..) => StatusCode::SERVICE_UNAVAILABLE,
            Self::NotAcceptable(..) => StatusCode::NOT_ACCEPTABLE,
            Self::ParameterError(..) | Self::InvalidName(..) => StatusCode::BAD_REQUEST,
            _ => StatusCode::NOT_FOUND,
        };
        (statuscode, Json(self)).into_response()
    }
}

/*
impl From<ClamError> for ApiError {
    fn from(value: ClamError) -> Self {
    }
}
*/

impl From<std::io::Error> for ApiError {
    fn from(value: std::io::Error) -> Self {
        match value.kind() {
            std::io::ErrorKind::NotFound => Self::NotFound("file not found on filesystem"),
            std::io::ErrorKind::PermissionDenied => {
                Self::PermissionDenied("permission denied on filesystem")
            }
            std::io::ErrorKind::NotSeekable => Self::InternalError("file not seekable"),
            std::io::ErrorKind::StorageFull => Self::InternalError("storage full"),
            std::io::ErrorKind::ReadOnlyFilesystem => Self::InternalError("read only filesystem"),
            _ => Self::InternalError("File I/O error"),
        }
    }
}

impl From<axum::Error> for ApiError {
    fn from(_value: axum::Error) -> Self {
        Self::InternalError("web framework error")
    }
}

use crate::config::{EndPoint, FileType, ServiceConfig};
use crate::error::ApiError;
use axum::body::Body;
use serde::Serialize;
use std::fs::{create_dir_all, remove_dir_all};
use std::path::{Path, PathBuf};
use tokio::fs::File;
use tokio_util::io::ReaderStream;

const FORBIDDEN_CHARS: [char; 7] = [' ', '/', '\\', '\'', '\'', '*', ','];

/// A project is a workspace for a user that holds input and output files
/// It is also tied to a particular endpoint (each endpoint holds its own projects)
pub struct Project<'a> {
    /// The identifier of the project
    id: String,

    user: String,

    endpoint: String,

    config: &'a ServiceConfig,
}

impl<'a> Project<'a> {
    /// Instantiate a project, does not yet create it
    pub fn new(
        id: impl Into<String>,
        user: impl Into<String>,
        endpoint: impl Into<String>,
        config: &'a ServiceConfig,
    ) -> Result<Self, ()> {
        let project = Self {
            id: id.into(),
            user: user.into(),
            endpoint: endpoint.into(),
            config,
        };
        if project.is_valid() {
            Ok(project)
        } else {
            Err(())
        }
    }

    /// Creates a project by writing the project directory to the filesystem
    pub fn create(&self) -> Result<(), std::io::Error> {
        let path = self.path();
        create_dir_all(path)?;
        Ok(())
    }

    /// Deletes a project by deleting the project directory and all it contains from the filesystem
    pub fn delete(&self) -> Result<(), std::io::Error> {
        let path = self.path();
        remove_dir_all(path)?;
        Ok(())
    }

    /// Checks whether a project is valid (valid ID, valid user, valid endpoint)
    /// These three components are encoded in the project path and must be safe
    pub fn is_valid(&self) -> bool {
        if self.id.is_empty() || self.user.is_empty() || self.endpoint.is_empty() {
            return false;
        }
        if self
            .id
            .as_str()
            .chars()
            .any(|c| FORBIDDEN_CHARS.contains(&c))
        {
            return false;
        }

        if self
            .user
            .as_str()
            .chars()
            .any(|c| FORBIDDEN_CHARS.contains(&c))
        {
            return false;
        }
        if self.id.as_str().find("..").is_some() {
            return false;
        }
        true
    }

    /// Returns the path to the project on the filesystem
    pub fn path(&self) -> PathBuf {
        let user: PathBuf = PathBuf::from(self.user.clone());
        let checksum = format!("{:x}", md5::compute(self.endpoint.as_str().as_bytes()));
        let endpoint: PathBuf = PathBuf::from(checksum);
        let id: PathBuf = PathBuf::from(self.id.clone());
        let mut p: PathBuf = self
            .config
            .rootdir()
            .as_ref()
            .map(|x| x.clone())
            .unwrap_or(".".into());
        p.push(user);
        p.push(endpoint);
        p.push(id);
        p
    }

    /// Returns the path of the specified output file if it indeed exists
    pub fn output_file(&self, filename: &str) -> Option<PathBuf> {
        let mut path = self.path();
        path.push(filename);
        if path.is_file() { Some(path) } else { None }
    }

    /// Returns the path of the specified input file if it indeed exists
    pub fn input_file(&self, parameter_id: &str, filename: &str) -> Option<PathBuf> {
        let mut path = self.path();
        path.push(parameter_id);
        path.push(filename);
        if path.is_file() { Some(path) } else { None }
    }

    /// Returns the body of a file so it can be streamed to the client, use with `input_file()` or `output_file()'
    pub async fn file_body(&self, filepath: &Path) -> Result<axum::body::Body, ApiError> {
        let file = File::open(filepath).await?;
        let stream = ReaderStream::new(file);
        let body = Body::from_stream(stream);
        Ok(body)
    }

    pub fn output_filetype(&self, filename: &str) -> Option<FileType> {
        todo!("return matching filetype for output file");
    }
}

#[derive(Debug, Clone, Serialize)]
/// Returned to the client in JSON as part of `ProjectResponse`
#[serde(tag = "stage", content = "data")]
pub enum ProjectStatus {
    /// The project is in staging mode, you can upload files and when done start it
    Staging { input_files: Vec<String> },
    /// Project is scheduled for execution (but not running yet)
    Scheduled,
    /// The project is running
    Running {
        progress: Option<u8>,
        message: String,
    },
    /// The project is done (either succesfully or with a runtime error)
    Done {
        success: bool,
        message: Option<String>,
        output_files: Vec<String>,
    },
}

/// Returns an index of projects **for a specific user and endpoint**
pub fn project_index(
    user: &str,
    endpoint: &EndPoint,
    config: &ServiceConfig,
) -> Result<Vec<String>, std::io::Error> {
    if user.chars().any(|c| FORBIDDEN_CHARS.contains(&c)) {
        return Err(std::io::Error::new(
            std::io::ErrorKind::InvalidData,
            "rejecting username to due invalid chars",
        ));
    }
    let user: PathBuf = PathBuf::from(user);
    let mut p: PathBuf = config
        .rootdir()
        .as_ref()
        .map(|x| x.clone())
        .unwrap_or(".".into());
    p.push(user);
    let endpoint_checksum = format!("{:x}", md5::compute(endpoint.path().as_str().as_bytes()));
    p.push(endpoint_checksum);
    if p.is_dir() {
        let mut projects = Vec::new();
        for entry in std::fs::read_dir(p)? {
            let dir = entry?;
            projects.push(dir.file_name().to_string_lossy().to_string());
        }
        Ok(projects)
    } else {
        Ok(Vec::new())
    }
}

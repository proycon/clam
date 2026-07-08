use crate::config::EndPoint;
use crate::config::ServiceConfig;
use std::fs::{create_dir_all, remove_dir_all};
use std::path::PathBuf;

const FORBIDDEN_CHARS: [char; 7] = [' ', '/', '\\', '\'', '\'', '*', ','];

/// A project is a workspace for a user that holds input and output files
/// It is also tied to a particular endpoint (each endpoint holds its own projects)
#[derive(Debug)]
pub struct Project {
    /// The identifier of the project
    id: String,

    user: String,

    endpoint: String,
}

impl Project {
    /// Instantiate a project, does not yet create it
    pub fn new(
        id: impl Into<String>,
        user: impl Into<String>,
        endpoint: impl Into<String>,
    ) -> Result<Self, ()> {
        let project = Self {
            id: id.into(),
            user: user.into(),
            endpoint: endpoint.into(),
        };
        if project.is_valid() {
            Ok(project)
        } else {
            Err(())
        }
    }

    /// Creates a project by writing the project directory to the filesystem
    pub fn create(&self, config: &ServiceConfig) -> Result<(), std::io::Error> {
        let path = self.path(config);
        create_dir_all(path)?;
        Ok(())
    }

    /// Deletes a project by deleting the project directory and all it contains from the filesystem
    pub fn delete(&self, config: &ServiceConfig) -> Result<(), std::io::Error> {
        let path = self.path(config);
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
    pub fn path(&self, config: &ServiceConfig) -> PathBuf {
        let user: PathBuf = PathBuf::from(self.user.clone());
        let checksum = format!("{:x}", md5::compute(self.endpoint.as_str().as_bytes()));
        let endpoint: PathBuf = PathBuf::from(checksum);
        let id: PathBuf = PathBuf::from(self.id.clone());
        let mut p: PathBuf = config
            .rootdir()
            .as_ref()
            .map(|x| x.clone())
            .unwrap_or(".".into());
        p.push(user);
        p.push(endpoint);
        p.push(id);
        p
    }
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

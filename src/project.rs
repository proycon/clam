use crate::config::ServiceConfig;
use std::fs::{create_dir_all, remove_dir_all};
use std::path::PathBuf;

const FORBIDDEN_CHARS: [char; 7] = [' ', '/', '\\', '\'', '\'', '*', ','];

/// A project is a workspace for a user that holds input and output files
/// It is also tied to a particular endpoint
#[derive(Debug)]
pub struct Project {
    /// The identifier of the project
    id: String,

    user: String,

    endpoint: String,
}

impl Project {
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

    pub fn create(&self, config: &ServiceConfig) -> Result<(), std::io::Error> {
        let path = self.path(config);
        create_dir_all(path)?;
        Ok(())
    }

    pub fn delete(&self, config: &ServiceConfig) -> Result<(), std::io::Error> {
        let path = self.path(config);
        remove_dir_all(path)?;
        Ok(())
    }

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

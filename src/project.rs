use crate::ParameterType;
use crate::config::{EndPoint, FileName, FileType, ServiceConfig};
use crate::error::ApiError;
use axum::body::Body;
use derive_getters::Getters;
use serde::Serialize;
use std::fs::{create_dir_all, remove_dir_all};
use std::hash::Hash;
use std::path::{Path, PathBuf};
use tokio::fs::File;
use tokio_util::io::ReaderStream;

const FORBIDDEN_CHARS: [char; 7] = [' ', '/', '\\', '\'', '\'', '*', ','];

#[derive(Getters, Clone, Eq, PartialEq, Hash)]
/// Uniquely identifies a project
pub struct ProjectKey {
    /// Project name, also used in URLs
    name: String,

    user: String,

    endpoint_index: usize,
}

impl ProjectKey {
    pub fn new(name: impl Into<String>, user: impl Into<String>, endpoint_index: usize) -> Self {
        Self {
            name: name.into(),
            user: user.into(),
            endpoint_index,
        }
    }
}

/// A project is a workspace for a user that holds input and output files
/// It is also tied to a particular endpoint (each endpoint holds its own projects)
#[derive(Getters, Clone)]
pub struct Project<'a> {
    key: ProjectKey,

    config: &'a ServiceConfig,
}

impl<'a> PartialEq for Project<'a> {
    fn eq(&self, other: &Self) -> bool {
        self.key == other.key
    }
}

impl<'a> Project<'a> {
    /// Instantiate a project, does not yet create it
    pub fn new(
        id: impl Into<String>,
        user: impl Into<String>,
        endpoint_index: usize,
        config: &'a ServiceConfig,
    ) -> Result<Self, ()> {
        let project = Self {
            key: ProjectKey {
                name: id.into(),
                user: user.into(),
                endpoint_index,
            },
            config,
        };
        if project.is_valid() {
            Ok(project)
        } else {
            Err(())
        }
    }

    pub fn name(&self) -> &str {
        self.key.name()
    }

    pub fn user(&self) -> &str {
        self.key.user()
    }

    pub fn endpoint(&self) -> &'a EndPoint {
        self.config
            .endpoints()
            .get(self.key.endpoint_index)
            .expect("endpoint must exist")
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
        if self.name().is_empty() || self.user().is_empty() {
            return false;
        }
        if self.name().chars().any(|c| FORBIDDEN_CHARS.contains(&c)) {
            return false;
        }

        if self.user().chars().any(|c| FORBIDDEN_CHARS.contains(&c)) {
            return false;
        }
        if self.name().find("..").is_some() {
            return false;
        }
        true
    }

    /// Returns the path to the project on the filesystem
    pub fn path(&self) -> PathBuf {
        let user: PathBuf = PathBuf::from(self.user());
        let checksum = format!(
            "{:x}",
            md5::compute(self.endpoint().path().as_str().as_bytes())
        );
        let endpoint: PathBuf = PathBuf::from(checksum);
        let id: PathBuf = PathBuf::from(self.name());
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

    /// Returns the URL to the project on the server
    pub fn url(&self) -> String {
        format!("{}{}", self.endpoint().path(), self.name())
    }

    pub fn exists(&self) -> bool {
        self.path().exists()
    }

    /// Returns the path of the specified output file if it indeed exists
    pub fn output_file(&self, filename: &str) -> Option<PathBuf> {
        let mut path = self.path();
        path.push(filename);
        if path.is_file() { Some(path) } else { None }
    }

    /// Returns the path of the specified input file if it indeed exists
    pub fn input_file(
        &self,
        parameter_id: &str,
        filename: &str,
        must_exist: bool,
    ) -> Option<PathBuf> {
        let mut path = self.path();
        path.push(parameter_id);
        path.push(filename);
        if path.is_file() || !must_exist {
            Some(path)
        } else {
            None
        }
    }

    pub fn create_parameter_dir(&self, parameter_id: &str) -> Result<PathBuf, std::io::Error> {
        let mut p = self.path();
        p.push(parameter_id);
        std::fs::create_dir_all(&p)?;
        Ok(p)
    }

    pub fn set_input_file(
        &self,
        parameter_id: &str,
        filename: &str,
        value: String,
    ) -> Result<(), std::io::Error> {
        let mut p = self.create_parameter_dir(parameter_id)?;
        p.push(parameter_id);
        std::fs::write(filename, value)
    }

    /// Returns the body of a file so it can be streamed to the client, use with `input_file()` or `output_file()'
    pub async fn file_body(&self, filepath: &Path) -> Result<axum::body::Body, ApiError> {
        let file = File::open(filepath).await?;
        let stream = ReaderStream::new(file);
        let body = Body::from_stream(stream);
        Ok(body)
    }

    pub fn input_filetype(&self, filename: &str) -> Option<&'a FileType> {
        for parameter in self.endpoint().parameters().iter() {
            if let ParameterType::File {
                filename: _,
                filetype,
                conflictresolution: _,
            } = parameter.r#type()
            {
                if parameter.validate_filename(filename).is_ok() {
                    return self.config.filetype(filetype.as_str());
                }
            }
        }
        None
    }

    pub fn input_parameter_filetype(
        &self,
        filename: &str,
    ) -> (Option<&'a str>, Option<&'a FileType>) {
        for parameter in self.endpoint().parameters().iter() {
            if let ParameterType::File {
                filename: _,
                filetype,
                conflictresolution: _,
            } = parameter.r#type()
            {
                if parameter.validate_filename(filename).is_ok() {
                    return (
                        Some(parameter.id()),
                        self.config.filetype(filetype.as_str()),
                    );
                }
            }
        }
        (None, None)
    }

    /// Returns the file type for a given output file
    pub fn output_filetype(&self, filename: &str) -> Option<&'a FileType> {
        for outputfile in self.endpoint().outputfiles() {
            match outputfile.filename() {
                FileName::Exact(name) => {
                    if name == filename {
                        return self.config.filetype(outputfile.r#type().as_str());
                    }
                }
                FileName::Pattern(pattern) => {
                    if pattern.is_match(filename) {
                        return self.config.filetype(outputfile.r#type().as_str());
                    }
                }
            }
        }
        None
    }

    /// Returns a list of output files, to be served as part of ProjectStatus (GET)
    pub fn output_files(&self) -> Vec<IoFile> {
        let mut output_files = Vec::new();
        if let Ok(dir_iter) = std::fs::read_dir(self.path()) {
            for entry in dir_iter {
                if let Ok(entry) = entry {
                    let path = entry.path();
                    if path.is_file() {
                        if let Ok(filename) = entry.file_name().into_string() {
                            if let Some(filetype) = self.output_filetype(filename.as_str()) {
                                output_files.push(IoFile {
                                    filetype: Some(filetype.clone()), //MAYBE TODO: not sure if I like so many clones of the same data (but reference not possible, tried)
                                    parameter: None,
                                    name: filename,
                                })
                            } else if self.endpoint().show_unknown_output() {
                                // by default we skip files that can not be identified as output, unless show_unknown_output is explicitly enabled
                                output_files.push(IoFile {
                                    filetype: None,
                                    parameter: None,
                                    name: filename,
                                })
                            }
                        }
                    }
                }
            }
        }
        output_files
    }

    /// Returns a list of input files (and associated filetype), served to the client as part of ProjectStatus (GET)
    pub fn input_files(&self) -> Vec<IoFile> {
        let mut input_files = Vec::new();
        for parameter in self.endpoint().parameters().iter() {
            if let ParameterType::File {
                filename,
                filetype,
                conflictresolution: _,
            } = parameter.r#type()
            {
                // first collect the actual files for this parameter
                let mut found_files: Vec<String> = Vec::new();
                let mut p = self.path();
                p.push(parameter.id());
                if let Ok(dir_iter) = std::fs::read_dir(p) {
                    for entry in dir_iter {
                        if let Ok(entry) = entry {
                            let path = entry.path();
                            if path.is_file() {
                                if let Ok(name) = entry.file_name().into_string() {
                                    found_files.push(name)
                                }
                            }
                        }
                    }
                }
                match filename {
                    FileName::Exact(name) => {
                        if found_files.contains(name) {
                            input_files.push(IoFile {
                                filetype: self.config.filetype(filetype).cloned(),
                                parameter: Some(parameter.id().clone()),
                                name: name.clone(),
                            })
                        }
                    }
                    FileName::Pattern(pattern) => {
                        let filetype = self.config.filetype(filetype);
                        for file in found_files {
                            if pattern.is_match(file.as_str()) {
                                input_files.push(IoFile {
                                    filetype: filetype.cloned(),
                                    parameter: Some(parameter.id().clone()),
                                    name: file,
                                })
                            }
                        }
                    }
                }
            }
        }
        input_files
    }
}

#[derive(Debug, Clone, Serialize)]
/// Returned to the client in JSON
#[serde(tag = "stage", content = "data")]
pub enum ProjectStatus {
    /// The project is in staging mode, you can upload files and when done start it
    Staging { input_files: Vec<IoFile> },
    /// Project is scheduled for execution (but not running yet)
    Scheduled,
    /// The project is running
    Running {
        progress: Option<u8>,
        statuslog: String,
    },
    /// The project is done (either succesfully or with a runtime error)
    Done {
        success: bool,
        statuslog: Option<String>,
        input_files: Vec<IoFile>,
        output_files: Vec<IoFile>,
    },
}

#[derive(Debug, Clone, Serialize)]
/// Returned to the client in JSON as part of ProjectStatus, used for both input and output files
pub struct IoFile {
    /// Filename
    name: String,

    /// For input files, this is always something
    parameter: Option<String>,

    filetype: Option<FileType>,
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

/*
    This modules contains data structures that are populated from the service configuration
*/

use crate::envsubst::*;
use crate::error::ClamError;
use derive_getters::Getters;
use serde::{Deserialize, Serialize};
use std::fmt::Debug;
use std::fs;
use std::io::Read;
use std::path::PathBuf;

#[derive(Deserialize, Serialize, Default, Getters)]
pub struct ServiceConfig {
    /// The version of the webservice, increment this on subsequent releases. Semantic versioning is strongly recommended.
    version: String,

    /// The Human-readable name of the webservice
    name: String,

    /// The host and port to listen on (`host:port`). Can also be overriden from the command-line at runtime.
    listen: Option<String>,

    /// A short human-readable description
    description: Option<String>,

    /// The authors of the webservice
    authors: Vec<String>,

    email: Option<String>,

    /// base URL where this webservice is served
    url: Option<String>,

    /// base path where the user files for the webservice are stored at runtime, must be writable by the user the clam runs as. Defaults to current working directory if not set.
    rootdir: Option<PathBuf>,

    /// URL for extra documentation
    documentation_url: Option<String>,

    /// Link to a source code repository
    sourcerepo: Option<String>,

    /// The license of the service, an SPDX compatible identifier is strongly recommended here
    license: Option<String>,

    filetypes: Vec<FileType>,
    viewers: Vec<Viewer>,

    endpoints: Vec<EndPoint>,

    auth: Option<AuthConfig>,

    /// CORS
    allow_origin: Option<String>,

    /// Maximum number of running jobs at the same time
    max_running_jobs: usize,

    /// Maximum number of jobs waiting in the queue, if full, HTTP 503 will be returned
    max_total_jobs: usize,

    /// External script to launch prior to accepting tasks.
    /// It can be used to do a system load check
    /// HTTP 503 will be returned if this script fails (= returns a non-zero exit code).
    pre_accept_script: Option<String>,
}

#[derive(Deserialize, Serialize, Default)]
pub struct AuthConfig {
    /// Path to a tab seperated file of usernames and hashed passwords for HTTP Basic Authentication.
    user_db: Option<String>,

    oauth_client_id: Option<String>,
    oauth_client_url: Option<String>,
    oauth_client_secret: Option<String>,
    oauth_token_url: Option<String>,
    oauth_scope: Option<String>,
}

#[derive(Deserialize, Serialize, Default)]
pub enum ServeMode {
    ///In action mode, a single response follows immediately upon a POST request. This assumes the job runs in limited time with singular output only (of a specific filetype). No file upload/download support.
    Action { filetype: String },

    ///In project mode, responses do not come immediately after a POST request but clients poll for status at regular intervals using a GET request and must first CREATE a project. This allows the job to run over long periods of time and allows (multiple) file-based output.
    #[default]
    Project,
}

#[derive(Deserialize, Serialize, Clone)]
#[serde(untagged)]
pub enum CommandArg {
    /// Literal static parameter passed at configuration time
    Literal(String),

    /// The argument comes from a parameter passed by the user at runtime
    FromParameter { parameter_id: String },
}

#[derive(Deserialize, Serialize, Default, Getters)]
pub struct EndPoint {
    /// The path where the endpoint is accessible, this also serves as the primary identifier for the endpoint. All paths must start with /
    path: String,

    name: String,
    description: Option<String>,

    mode: ServeMode,

    /// Public endpoints are available without authentication
    public: bool,

    /// Command to invoke (mediated by dispatcher)
    command: String,

    /// Arguments to pass to the command
    args: Vec<CommandArg>,

    parameters: Vec<Parameter>,

    errorstates: Vec<ErrorState>,

    /// Regular expression to select which stderr lines propagate to the webinterface's status message
    status_pattern: Option<String>,
}

#[derive(Clone, Debug, Deserialize, Serialize, Default)]
pub enum FileConflictResolution {
    // Reject input files which don't match the pattern
    #[default]
    Reject,

    //Coerce an input file into a pattern when it doesn't matches
    Coerce,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(tag = "parametertype")]
pub enum ParameterType {
    /// Open-valued text
    String {
        #[serde(default)]
        maxlength: Option<usize>,
        #[serde(default)]
        validation_pattern: Option<String>,

        #[serde(default)]
        default: Option<String>,
    },

    /// Numeric value
    Int {
        #[serde(default)]
        min: Option<isize>,
        #[serde(default)]
        max: Option<isize>,

        #[serde(default)]
        default: Option<isize>,
    },

    /// Numeric value
    Float {
        #[serde(default)]
        min: Option<f64>,
        #[serde(default)]
        max: Option<f64>,

        #[serde(default)]
        default: Option<f64>,
    },

    /// Boolean value
    Bool {
        #[serde(default)]
        invert: Option<bool>,

        #[serde(default)]
        default: Option<bool>,
    },

    /// File
    File {
        name: FileName,
        filetype: String,

        /// Coerce input file into pattern even when it doesn't match
        conflictresolution: FileConflictResolution,
    },

    /// Selection amongst predefined values
    Selection {
        choices: Vec<String>,
        /// Allow multiple choices
        #[serde(default)]
        multiple: bool,

        #[serde(default)]
        default: Option<Vec<String>>,
    },
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct Parameter {
    /// Identifier for the parameter, used as variable name in HTTP requests
    id: String,

    /// The type of parameter
    r#type: ParameterType,

    /// Human-readable name for the parameter
    name: String,

    /// Human-readable description of the parameter
    description: Option<String>,

    /// Is this parameter required?
    required: bool,

    /// Allow multiple of these?
    multiple: bool,

    /// the full parameter flag that is used to pass this parameter to the underlying tool, this includes any = sign
    flag: Option<String>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(tag = "nametype", content = "value")]
pub enum FileName {
    /// Exact filename
    Exact(String),
    /// Regular expression to capture file(s)
    Pattern(String),
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct FileType {
    /// Internal ID
    id: String,

    /// Human-readable name
    name: String,

    /// Content-Type header as returned in HTTP responses
    contenttype: String,

    /// URL to forward to
    viewers: Vec<Viewer>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct Viewer {
    id: String,

    /// Human readable name
    name: String,

    r#type: ViewerType,

    /// Parameters to pass to the command or to the URL
    args: Vec<ViewerArg>,
}

#[derive(Deserialize, Serialize, Clone, Debug)]
#[serde(untagged)]
pub enum ViewerArg {
    /// Literal static parameter passed at configuration time
    Literal(String),

    /// The argument comes from a parameter passed by the user
    FromParameter { parameter_id: String },
    /// The argument is a **publicly accessible** anonimized URL where the file can be obtained (for use with `ViewerType::URL`)
    PublicDownloadURL,

    /// The argument is the path to the local file (for use with `ViewerType::Command`)
    LocalPath,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub enum ViewerType {
    Command(String),
    URL(String),
}

#[derive(Clone, Debug, Deserialize, Serialize)]
pub struct ErrorState {
    code: u8,
    message: String,
}

impl ServiceConfig {
    /// Parse the full configuration from a TOML string
    pub fn from_toml_str(tomlstr: &str) -> Result<Self, ClamError> {
        let config: Self = toml::from_str(tomlstr).map_err(|e| ClamError::ConfigError(e))?;
        Ok(config)
    }

    /// Parse the full configuration from a TOML file
    pub fn from_file(filename: &str) -> Result<Self, ClamError> {
        let configdata = fs::read_to_string(filename).map_err(|e| ClamError::IoError(e))?;
        Self::from_toml_str(configdata.as_str())
    }

    /// Parse the full configuration from stdin
    pub fn from_stdin() -> Result<Self, ClamError> {
        let mut configdata = String::new();
        std::io::stdin()
            .lock()
            .read_to_string(&mut configdata)
            .map_err(|e| ClamError::IoError(e))?;
        Self::from_toml_str(configdata.as_str())
    }

    pub fn with_listen(mut self, host_and_port: impl Into<String>) -> Self {
        self.listen = Some(host_and_port.into());
        self
    }
}

// TODO: I might decide to toss this EnvSubst all away and just rely on external envsubst instead
impl Envsubst for ServiceConfig {
    fn envsubst(&mut self) -> Result<(), ClamError> {
        envsubst(&mut self.version, EnvsubstMode::ErrorIfMissing)?;
        envsubst(&mut self.name, EnvsubstMode::ErrorIfMissing)?;
        if let Some(Err(e)) = self
            .description
            .as_mut()
            .map(|v| envsubst(v, EnvsubstMode::ErrorIfMissing))
        {
            return Err(e);
        }
        if let Some(Err(e)) = self
            .email
            .as_mut()
            .map(|v| envsubst(v, EnvsubstMode::ErrorIfMissing))
        {
            return Err(e);
        }
        if let Some(Err(e)) = self
            .url
            .as_mut()
            .map(|v| envsubst(v, EnvsubstMode::ErrorIfMissing))
        {
            return Err(e);
        }
        if let Some(Err(e)) = self
            .documentation_url
            .as_mut()
            .map(|v| envsubst(v, EnvsubstMode::ErrorIfMissing))
        {
            return Err(e);
        }
        if let Some(Err(e)) = self
            .sourcerepo
            .as_mut()
            .map(|v| envsubst(v, EnvsubstMode::ErrorIfMissing))
        {
            return Err(e);
        }
        if let Some(Err(e)) = self
            .license
            .as_mut()
            .map(|v| envsubst(v, EnvsubstMode::ErrorIfMissing))
        {
            return Err(e);
        }
        for endpoint in self.endpoints.iter_mut() {
            endpoint.envsubst()?;
        }
        Ok(())
    }
}

impl Envsubst for EndPoint {
    fn envsubst(&mut self) -> Result<(), ClamError> {
        envsubst(&mut self.name, EnvsubstMode::ErrorIfMissing)?;
        envsubst(&mut self.path, EnvsubstMode::ErrorIfMissing)?;
        if let Some(Err(e)) = self
            .description
            .as_mut()
            .map(|v| envsubst(v, EnvsubstMode::ErrorIfMissing))
        {
            return Err(e);
        }
        Ok(())
    }
}

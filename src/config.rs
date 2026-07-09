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

#[derive(Deserialize, Serialize, Default, Getters, Clone)]
pub struct ServiceConfig {
    /// The version of the webservice, increment this on subsequent releases. Semantic versioning is strongly recommended.
    version: String,

    /// The Human-readable name of the webservice
    name: String,

    /// The host and port to listen on (`host:port`). Can also be overriden from the command-line at runtime.
    listen: Option<String>,

    /// Description of the service, supports CommonMark syntax. (for human end-users)
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

    /// The license of the service, has fields name, id (SPDX identifier) and URL.
    license: Option<utoipa::openapi::License>,

    /// The contact person/organisation for this deployment of the webservice (may differ from the actual authors!)
    contact: Option<utoipa::openapi::Contact>,

    /// URL for the Terms of Service for this API
    termsofservice: Option<String>,

    /// File type definitions
    filetypes: Vec<FileType>,

    /// Viewer definitions, used by file types
    viewers: Vec<Viewer>,

    /// Output file definitions  (ties matching filenames to filetypes)
    outputfiles: Vec<OutputFile>,

    /// Endpoint configuration
    endpoints: Vec<EndPoint>,

    #[serde(default)]
    auth: AuthConfig,

    /// CORS
    allow_origin: Option<String>,

    #[serde(default)]
    dispatcher: DispatcherConfig,
}

#[derive(Deserialize, Serialize, Clone, Default, Getters)]
pub struct DispatcherConfig {
    /// Maximum number of running jobs at the same time
    max_running_jobs: usize,

    /// Maximum number of jobs waiting in the queue, if full, HTTP 503 will be returned
    max_total_jobs: usize,

    /// External script to launch prior to accepting tasks.
    /// It can be used to do a system load check
    /// HTTP 503 will be returned if this script fails (= returns a non-zero exit code).
    pre_accept_script: Option<String>,
}

#[derive(Deserialize, Serialize, Default, Clone, Getters)]
/// Authorization Configuration, points to external files that holds credentials so it is
/// easier to separate the service configuration from secret configurations.
pub struct AuthConfig {
    /// Path to a tab seperated file of usernames and hashed passwords for HTTP Basic Authentication.
    user_file: Option<String>,

    /// Path to a toml file holding the OAuth2 credentials/configuration for OAuth2/OpenID Connect authentication
    oauth_config_file: Option<String>,

    /// The URL to redirect to after succesful authentication
    postauth_url: Option<String>,
}

#[derive(Deserialize, Serialize, Default, Clone, Getters)]
pub struct OAuthCredentials {
    /// URL from where to obtain the OpenID configuration at run-time, is usually something like https://example.com/.well-known/openid-configuration
    /// and obtained once when the service starts
    pub(crate) openid_configuration_url: String,
    pub(crate) openid_redirect_url: String,

    pub(crate) oauth_client_id: String,
    pub(crate) oauth_client_secret: String,

    #[serde(default = "default_cookie_path")]
    pub(crate) cookie_path: String,

    #[serde(default)]
    pub(crate) oauth_scope: Vec<String>,
}

fn default_cookie_path() -> String {
    "/".into()
}

impl OAuthCredentials {
    /// Is OAuth enabled or not?
    pub fn enabled(&self) -> bool {
        !self.openid_configuration_url.is_empty()
            && !self.oauth_client_id.is_empty()
            && !self.oauth_client_secret.is_empty()
            && !self.openid_redirect_url.is_empty()
    }
}

#[derive(Deserialize, Serialize, Default, Clone)]
pub enum EndPointMode {
    /// In action mode, a single response follows immediately upon a POST request. This assumes the job runs in limited time with singular output only. No file upload/download support.
    /// A GET on this endpoint (requesting HTML) presents the interface for that action.
    Action,

    /// In project mode, responses do not come immediately after a POST request but clients poll for status at regular intervals using a GET request and must first CREATE a project and optionally PUT files.
    /// Users can DELETE projects when done, or leave them to come back later.
    /// This allows the job to run over long periods of time and allows (multiple) file-based output.
    /// All endpoint paths are suffixed with the project ID
    /// The GET endpoint presents the staging area (files), an in progress state, or the output files, depending on the state of the project
    #[default]
    Project,

    /// The Porch is a publicly accessible endpoint (unauthenticated) that gives information over the service and allows users to continue
    /// to the authenticated sections
    /// It is typically served at path `/` and used as a landing page.
    Porch,

    /// Provides a list of project or action endpoints. This is what people will see after logging in (if such an endpoint is defined)
    Index,
}

#[derive(Deserialize, Serialize, Clone)]
#[serde(untagged)]
pub enum CommandArg {
    /// Literal static parameter passed at configuration time
    Literal(String),

    /// The argument comes from a parameter passed by the user at runtime
    FromParameter { parameter_id: String },
}

#[derive(Deserialize, Serialize, Default, Getters, Clone)]
pub struct EndPoint {
    /// The path where the endpoint is accessible, this also serves as the primary identifier for the endpoint. All paths must start with /
    path: String,

    /// Human-readable name or title of the endpoint
    name: String,

    /// Short summary of the endpoint (for human end-users)
    summary: Option<String>,

    /// Larger description of the endpoint, supports CommonMark syntax. (for human end-users)
    description: Option<String>,

    mode: EndPointMode,

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

    /// Return type for the endpoint, used for actions
    filetype: Option<String>,
    // One or more endpoints that can come after this, so for which the output of this endpoint acts at the input, the user can choose one to continue
    //next: Vec<String>, //implement later

    // One or more endpoints that come before this endpoint, so the output of that endpoint acts as the input for this one. These are possible dependencies that the user can run before tis one.
    //before: Vec<String>, //implement later
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
        filename: FileName,

        /// Should match with an id from the filetypes
        filetype: String,

        /// Coerce input file into pattern even when it doesn't match
        #[serde(default)]
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

#[derive(Clone, Debug, Deserialize, Serialize, Getters)]
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

#[derive(Clone, Debug, Deserialize, Serialize, Getters)]
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

#[derive(Clone, Debug, Deserialize, Serialize, Getters)]
pub struct OutputFile {
    /// name of the type of output
    name: String,

    /// Filetype, corresponds with an ID in filetypes
    r#type: String,

    /// Filename, output files are assigned this OutputFile when this matches
    filename: FileName,
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

    /// Get a filetype object by name
    pub fn get_filetype(&self, filetype: &str) -> Option<&FileType> {
        for f in self.filetypes() {
            if f.id == filetype {
                return Some(f);
            }
        }
        None
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

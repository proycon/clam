use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::fmt::Debug;

#[derive(Deserialize, Serialize, Default)]
struct Service {
    id: String,
    version: String,
    name: String,
    description: Option<String>,
    authors: Vec<String>,
    email: Option<String>,
    license: Option<String>,

    filetypes: Vec<FileType>,
    viewers: Vec<Viewer>,

    endpoints: Vec<Endpoint>,
}

#[derive(Deserialize, Serialize, Default)]
struct Endpoint {
    path: String,

    name: String,
    description: Option<String>,

    ///In batch mode, responses do not come immediately but status is polled-for at regular intervals
    batch: bool,

    /// Command to invoke (mediated by dispatcher)
    command: String,

    /// Arguments to pass to the command
    args: Vec<String>,

    parameters: Vec<Parameter>,

    errorstates: Vec<ErrorState>,

    /// Regular expression to select which stderr lines propagate to the webinterface's status message
    status_pattern: Option<String>,

    /// Path to a tab seperated file of usernames and hashed passwords for HTTP Basic Authentication
    user_db: Option<String>,

    oauth_client_id: Option<String>,
    oauth_client_url: Option<String>,
    oauth_client_secret: Option<String>,
    oauth_token_url: Option<String>,
    oauth_scope: Option<String>,

    /// CORS
    allow_origin: Option<String>,

    /// Maximum number of workers that may at the same time
    max_workers: usize,

    /// Maximum number of tasks waiting in the queue, if full, HTTP 503 will be returned
    max_queue_size: usize,

    /// External script to launch prior to accepting tasks.
    /// It can be used to do a system load check
    /// HTTP 503 will be returned if this script fails.
    pre_accept_script: Option<String>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
enum ParameterType {
    /// Open-valued text
    String {
        maxlength: Option<usize>,
        validation_pattern: Option<String>,
    },

    /// Numeric value
    Int {
        min: Option<isize>,
        max: Option<isize>,
    },

    /// Boolean value
    Bool { invert: Option<bool> },

    /// File
    File { name: FileName, r#type: String },

    /// Selection amongst predefined values
    Selection {
        choices: Vec<String>,
        /// Allow multiple choices
        multiple: bool,
    },
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct Parameter {
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

    /// the parameter flag that is used to pass this parameter to the underlying tool, including any = sign
    flag: Option<String>,

    /// Default value
    default: Option<Value>,

    /// Actual value
    value: Option<Value>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
enum FileName {
    /// Exact filename
    Exact(String),
    /// Regular expression to capture file(s)
    Pattern(String),
}

#[derive(Clone, Debug)]
struct InputFile {
    name: FileName,
    filetype: FileType,
}

struct OutputFile {
    ///Regular expression to capture output file(s)
    pattern: String,
    filetype: FileType,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct FileType {
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
struct Viewer {
    id: String,

    /// Human readable name
    name: String,

    r#type: ViewerType,

    /// Parameters to pass to the command or to the URL, the variable $FILE_URL is reserved as a **publicly accessible** anonimized URL where the file can be obtained, the variable $FILE is the local file (for `ViewerType::Command`)
    args: Vec<String>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
enum ViewerType {
    Command(String),
    URL(String),
}

#[derive(Clone, Debug, Deserialize, Serialize)]
struct ErrorState {
    code: u8,
    message: String,
}

impl Service {
    fn new(id: String) -> Self {
        Self {
            id,
            ..Default::default()
        }
    }
}

fn main() {
    println!("Hello, world!");
}

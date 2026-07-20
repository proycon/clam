use crate::auth::CurrentUser;
use crate::config::{CommandArg, EndPoint, FileName, ParameterType};
use crate::dispatcher::Message;
use crate::project::Project;
use crate::project::ProjectKey;
use crate::state::ServiceState;
use derive_getters::Getters;
use nix::sys::signal::{Signal, kill};
use nix::unistd::Pid;
use regex::Regex;
use std::collections::HashMap;
use std::fs;
use std::io::{BufRead, BufReader, Read};
use std::sync::mpsc::Sender;

pub type JobId = usize;

#[derive(Debug, Clone, Getters)]
pub struct Job {
    /// Job identifier
    id: JobId,

    /// The particular endpoint in the service configuration this job is associated with (by index)
    endpoint_index: usize,

    /// The particular project this job is associated with (if any, actions have no projects)
    project: Option<String>,

    /// PID of underlying process
    pid: Option<u32>,

    /// The particular user this job is associated with (may be 'anonymous')
    user: String,

    /// command to run (just the executable, without any arguments)
    command: String,

    args: Vec<String>,

    status_pattern: Option<Regex>,

    /// Progress indicator (picks up percentages in lines extracted by `status_pattern`)
    progress: Option<u8>,

    /// status log (an extract of stderr matching the status_pattern), for running jobs
    statuslog: String,

    /// Holds exit status (only for done jobs)
    exitstatus: Option<i32>,
    /// Holds standard output (only for done jobs)
    output: Option<String>,
    /// Holds stderr output (only for done jobs)
    error: Option<String>,
}

impl Job {
    pub fn new<'a>(
        state: &ServiceState,
        endpoint_index: usize,
        project: Option<&Project<'a>>,
        user: &CurrentUser,
        request_params: HashMap<String, String>,
    ) -> Self {
        let endpoint = state.endpoint(endpoint_index);
        let mut error = None;
        let args = match Self::collect_arguments(endpoint, project, request_params) {
            Ok(args) => args,
            Err(e) => {
                error = Some(e);
                Vec::new()
            }
        };
        Self {
            id: rand::random_range(1..usize::MAX),
            endpoint_index,
            project: project.map(|x| x.name().to_string()),
            user: user.as_str().to_string(),
            command: endpoint.command().into(),
            progress: None,
            status_pattern: endpoint.status_pattern().clone(),
            pid: None,
            output: None,
            error,
            statuslog: String::new(),
            exitstatus: None,
            args,
        }
    }

    /// Processes request parameters and transforms them to command line arguments, validating all parameters in the process
    fn collect_arguments<'a>(
        endpoint: &EndPoint,
        project: Option<&Project<'a>>,
        request_params: HashMap<String, String>,
    ) -> Result<Vec<String>, String> {
        let mut args = Vec::new();
        let mut error = String::new();
        for arg in endpoint.args() {
            match arg {
                CommandArg::Literal(arg) => args.push(arg.clone()),
                CommandArg::FromParameter { parameter_id } => {
                    if let Some(parameter) = endpoint.parameter(parameter_id) {
                        let mut skip = false;
                        if let Some(value) = request_params.get(parameter.id()) {
                            // validate the value
                            match parameter.r#type() {
                                ParameterType::String {
                                    maxlength,
                                    validation_pattern,
                                    default: _,
                                } => {
                                    if let Some(maxlength) = maxlength
                                        && value.len() > *maxlength
                                    {
                                        error += &format!(
                                            "parameter {}: maximum length exceeded ({})\n",
                                            parameter.id(),
                                            maxlength
                                        );
                                    }
                                    if let Some(regex) = validation_pattern {
                                        if !regex.is_match(value) {
                                            error += &format!(
                                                "parameter {}: did not match against validation pattern ({})\n",
                                                parameter.id(),
                                                regex
                                            );
                                        }
                                    }
                                }
                                ParameterType::Int {
                                    min,
                                    max,
                                    default: _,
                                } => {
                                    if let Ok(v) = value.parse::<isize>() {
                                        if let Some(min) = min
                                            && v < *min
                                        {
                                            error += &format!(
                                                "parameter {}: value too low (< {})\n",
                                                parameter.id(),
                                                min
                                            );
                                        }
                                        if let Some(max) = max
                                            && v > *max
                                        {
                                            error += &format!(
                                                "parameter {}: value too high (> {})\n",
                                                parameter.id(),
                                                max
                                            );
                                        }
                                    } else {
                                        error += &format!(
                                            "parameter {}: expected integer\n",
                                            parameter.id()
                                        );
                                    }
                                }
                                ParameterType::Float {
                                    min,
                                    max,
                                    default: _,
                                } => {
                                    if let Ok(v) = value.parse::<f64>() {
                                        if let Some(min) = min
                                            && v < *min
                                        {
                                            error += &format!(
                                                "parameter {}: value too low (< {})\n",
                                                parameter.id(),
                                                min
                                            );
                                        }
                                        if let Some(max) = max
                                            && v > *max
                                        {
                                            error += &format!(
                                                "parameter {}: value too high (> {})\n",
                                                parameter.id(),
                                                max
                                            );
                                        }
                                    } else {
                                        error += &format!(
                                            "parameter {}: expected integer\n",
                                            parameter.id()
                                        );
                                    }
                                }
                                ParameterType::Bool { invert, .. } => {
                                    let v = value == "1"
                                        || value == "yes"
                                        || value == "enabled"
                                        || value == "true"
                                        || value == "True"
                                        || value == "TRUE";
                                    if (v && invert.is_none() || invert == &Some(false))
                                        || invert == &Some(true)
                                    {
                                        if let Some(flag) = parameter.flag() {
                                            args.push(flag.clone());
                                        }
                                    }
                                    skip = true;
                                }
                                ParameterType::File { filename, .. } => {
                                    //a value for the file was provided, rather than it having been uploaded independently earlier
                                    //this is acceptable only if an exact filename and a project is associated; we will use this value as the contents of the file and create (or overwrite!) it
                                    if let Some(project) = project {
                                        if let FileName::Exact(filename) = filename {
                                            if let Some(filepath) = project.input_file(
                                                parameter.id().as_str(),
                                                filename.as_str(),
                                            ) {
                                                if let Err(e) = fs::write(filepath, value) {
                                                    error += &format!(
                                                        "parameter {}: internal file I/O error {}",
                                                        parameter.id(),
                                                        e
                                                    );
                                                }
                                            }
                                        } else {
                                            error += &format!(
                                                "parameter {}: file parameter must be provided separately in an earlier upload stage rather than in this request\n",
                                                parameter.id()
                                            );
                                        }
                                    } else {
                                        //probably unreachable, but better safe than sorry:
                                        error += &format!(
                                            "parameter {}: file parameter is invalid on action endpoints (internal configuration error!)\n",
                                            parameter.id()
                                        );
                                    }
                                }
                                ParameterType::Selection {
                                    choices,
                                    multiple,
                                    default: _,
                                } => {
                                    if *multiple {
                                        for choice in value.split(",") {
                                            if !choices.iter().any(|c| c == choice) {
                                                error += &format!(
                                                    "parameter {}: value must be one of {}, multiple comma-separated values allowed\n",
                                                    parameter.id(),
                                                    choices.join(", ")
                                                );
                                                break; //don't pile up errors if there are multiple mismatches for this same value
                                            }
                                        }
                                    } else {
                                        if !choices.contains(&value) {
                                            error += &format!(
                                                "parameter {}: value must be one of {}\n",
                                                parameter.id(),
                                                choices.join(", ")
                                            );
                                        }
                                    }
                                }
                            }
                            if error.is_empty() && !skip {
                                if let Some(flag) = parameter.flag() {
                                    if flag.chars().last() == Some('=') {
                                        skip = true;
                                        args.push(format!("{}{}", flag, value));
                                    } else {
                                        args.push(flag.clone());
                                    }
                                }
                                if !skip {
                                    args.push(value.clone());
                                }
                            }
                        } else {
                            // we got no request value, see if we can extract a default value:
                            let value: Option<String> = match parameter.r#type() {
                                ParameterType::String {
                                    default: Some(default),
                                    ..
                                } => Some(default.clone()),
                                ParameterType::Int {
                                    default: Some(default),
                                    ..
                                } => Some(format!("{}", default)),
                                ParameterType::Float {
                                    default: Some(default),
                                    ..
                                } => Some(format!("{}", default)),
                                ParameterType::File { .. } => {
                                    if parameter.required() {
                                        //check if the file was uploaded, we expect at least one match
                                        if let Some(project) = project {
                                            let mut p = project.path();
                                            p.push(parameter.id());
                                            let mut file_found = false;
                                            if let Ok(dir_iter) = std::fs::read_dir(p) {
                                                for entry in dir_iter {
                                                    if let Ok(entry) = entry {
                                                        let path = entry.path();
                                                        if path.is_file() {
                                                            file_found = true;
                                                        }
                                                    }
                                                }
                                            }
                                            if !file_found {
                                                error += &format!(
                                                    "parameter {}: missing required parameter\n",
                                                    parameter.id().as_str()
                                                );
                                            }
                                        } else {
                                            //probably unreachable, but better safe than sorry:
                                            error += &format!(
                                                "parameter {}: file parameter is invalid on action endpoints (internal configuration error!)\n",
                                                parameter.id()
                                            );
                                        }
                                    }
                                    None
                                }
                                ParameterType::Selection {
                                    default: Some(default),
                                    ..
                                } => Some(format!("{}", default.join(","))),
                                _ => {
                                    if parameter.required() {
                                        error += &format!(
                                            "parameter {}: missing required parameter\n",
                                            parameter.id().as_str()
                                        );
                                    }
                                    None
                                }
                            };

                            // if we have a value and no errors, populate the arguments vector
                            if error.is_empty()
                                && !skip
                                && let Some(value) = value
                            {
                                if let Some(flag) = parameter.flag() {
                                    if flag.chars().last() == Some('=') {
                                        skip = true;
                                        args.push(format!("{}{}", flag, value));
                                    } else {
                                        args.push(flag.clone());
                                    }
                                }
                                if !skip {
                                    args.push(value.clone());
                                }
                            }
                        }
                    } else {
                        error += &format!(
                            "parameter {}: internal configuration error, non-existing parameter referenced!\n",
                            parameter_id,
                        );
                    }
                }
            }
        }
        if !error.is_empty() {
            Err(error)
        } else {
            Ok(args)
        }
    }

    pub fn set_output(&mut self, output: String) {
        self.output = Some(output);
    }

    pub fn set_error(&mut self, error: String) {
        self.error = Some(error);
    }

    pub fn set_exitstatus(&mut self, code: i32) {
        self.exitstatus = Some(code);
    }

    /// Returns the project key, an aggregate encoding endpoint, user and project and used by the project_job_map
    pub fn projectkey(&self) -> Option<ProjectKey> {
        if let Some(project) = self.project() {
            Some(ProjectKey::new(
                project,
                self.user.clone(),
                self.endpoint_index,
            ))
        } else {
            None
        }
    }

    pub fn log(&mut self, message: &str) {
        self.statuslog.push_str(message);
    }

    pub fn set_progress(&mut self, progress: u8) {
        self.progress = Some(progress);
    }

    /// Spawns the job (consumes it)
    /// This spawns a lightweight monitoring thread (native thread) which in turn spawns a child process
    pub fn spawn(self, dispatcherchannel: Sender<Message>) -> std::thread::JoinHandle<()> {
        std::thread::spawn(move || {
            match std::process::Command::new(self.command)
                .args(self.args)
                .stdout(std::process::Stdio::piped())
                .stderr(std::process::Stdio::piped())
                .spawn()
            {
                Ok(mut child) => {
                    if let Err(e) = dispatcherchannel.send(Message::StartedJob {
                        id: self.id,
                        pid: child.id(),
                    }) {
                        eprintln!("ERROR: Dispatcher send failure on start: {}", e)
                    }

                    let mut stderr = child.stderr.take().unwrap();
                    let mut stdout = child.stdout.take().unwrap();
                    let job_id = self.id;
                    let dispatcherchannel2 = dispatcherchannel.clone();

                    let error = if let Some(status_pattern) = self.status_pattern {
                        // we spawn another thread to monitor stderr for the status pattern and send updates when this matches
                        // we also collect all of stderr
                        let stderr_thread = std::thread::spawn(move || {
                            let mut full_stderr = String::new();

                            for line in BufReader::new(stderr).lines() {
                                match line {
                                    Ok(line) => {
                                        full_stderr.push_str(&line);
                                        full_stderr.push('\n');

                                        if status_pattern.is_match(line.as_str()) {
                                            let _ = dispatcherchannel2
                                                .send(Message::StatusLog(job_id, line));
                                        }
                                    }
                                    Err(e) => {
                                        full_stderr
                                            .push_str(&format!("Error reading stderr: {}\n", e));
                                        break;
                                    }
                                }
                            }

                            full_stderr
                        });

                        stderr_thread
                            .join()
                            .unwrap_or_else(|_| "Failed to read stderr".to_string())
                    } else {
                        // Collect all stderr (blocks until process exists)
                        let mut error = String::new();
                        if let Err(_) = stderr.read_to_string(&mut error) {
                            error = "Process stderr is invalid UTF-8!".to_string();
                        }
                        error
                    };

                    // Collect all stdout (blocks until process exists)
                    let mut output = String::new();
                    if let Err(_) = stdout.read_to_string(&mut output) {
                        output = "Process stdout is invalid UTF-8!".to_string();
                    }

                    let exitstatus = child.wait().unwrap();

                    if let Err(e) = dispatcherchannel.send(Message::FinishJob {
                        id: self.id,
                        exitstatus,
                        output,
                        error,
                    }) {
                        eprintln!("ERROR: Dispatcher send failure: {}", e)
                    }
                }
                Err(e) => {
                    if let Err(e2) = dispatcherchannel.send(Message::FailStartJob {
                        id: self.id,
                        error: format!("{}", e),
                    }) {
                        eprintln!("ERROR: Dispatcher error send failure: {}", e2)
                    }
                }
            }
        })
    }

    pub fn kill(&self) {
        if let Some(pid) = self.pid {
            let _ = kill(Pid::from_raw(pid as i32), Signal::SIGTERM); //sigterm asks nicely and assumes underlying processes comply (eventually)
        }
    }

    pub fn set_pid(&mut self, pid: u32) {
        self.pid = Some(pid);
    }

    pub fn wait(&self) {
        if let Some(pid) = self.pid {
            let _ = kill(Pid::from_raw(pid as i32), None);
        }
    }
}

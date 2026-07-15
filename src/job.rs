use crate::auth::CurrentUser;
use crate::dispatcher::Message;
use crate::project::ProjectKey;
use crate::state::ServiceState;
use axum::http::HeaderMap;
use core::usize;
use derive_getters::Getters;
use nix::errno::Errno;
use nix::sys::signal::{Signal, kill};
use nix::unistd::Pid;
use regex::Regex;
use std::collections::HashSet;
use std::io::{BufRead, BufReader, Read};
use std::sync::mpsc::Sender;
use std::thread::JoinHandle;
use std::time::Duration;

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

    /// command
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
    pub fn new(
        state: &ServiceState,
        endpoint_index: usize,
        project: Option<String>,
        user: &CurrentUser,
        headers: &HeaderMap,
    ) -> Self {
        let endpoint = state.endpoint(endpoint_index);
        //TODO: process command and arguments (replace build time parameters with run-time parameters)
        let command: String = endpoint.command().into();
        let args = Vec::new();
        Self {
            id: rand::random_range(1..usize::MAX),
            endpoint_index,
            project,
            user: user.as_str().to_string(),
            command,
            progress: None,
            status_pattern: endpoint.status_pattern().clone(),
            pid: None,
            output: None,
            error: None,
            statuslog: String::new(),
            exitstatus: None,
            args,
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
            kill(Pid::from_raw(pid as i32), Signal::SIGTERM); //sigterm asks nicely and assumes underlying processes comply (eventually)
        }
    }

    pub fn set_pid(&mut self, pid: u32) {
        self.pid = Some(pid);
    }

    pub fn wait(&self) {
        if let Some(pid) = self.pid {
            kill(Pid::from_raw(pid as i32), None);
        }
    }
}

pub async fn wait_for_pids(pids: Vec<u32>) {
    //wait until all pids in the lists are gone/done
    let mut pids: HashSet<Pid> = pids.iter().map(|&pid| Pid::from_raw(pid as i32)).collect();

    while !pids.is_empty() {
        pids.retain(|pid| match kill(*pid, None) {
            Ok(()) => true,             // Process still exists.
            Err(Errno::EPERM) => true,  // Exists, but we lack permission.
            Err(Errno::ESRCH) => false, // Process no longer exists.
            Err(_) => true,             // Unexpected error; keep trying.
        });

        if !pids.is_empty() {
            tokio::time::sleep(Duration::from_millis(100)).await;
        }
    }
}

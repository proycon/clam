use crate::auth::CurrentUser;
use crate::dispatcher::Message;
use crate::state::ServiceState;
use axum::http::HeaderMap;
use core::usize;
use derive_getters::Getters;
use nix::errno::Errno;
use nix::sys::signal::{Signal, kill};
use nix::unistd::Pid;
use std::collections::HashSet;
use std::sync::mpsc::Sender;
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
            command: endpoint.command().into(),
            pid: None,
            output: None,
            error: None,
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
            Some(ProjectKey {
                endpoint: self.endpoint_index,
                user: self.user.clone(),
                project: project.clone(),
            })
        } else {
            None
        }
    }

    /// Spawns the job (consumes it)
    /// This spawns a lightweight monitoring thread (native thread) which in turn spawns a child process
    pub fn spawn(self, dispatcherchannel: Sender<Message>) {
        std::thread::spawn(move || {
            match std::process::Command::new(self.command)
                .args(self.args)
                .stdout(std::process::Stdio::piped())
                .stderr(std::process::Stdio::piped())
                .spawn()
            {
                Ok(child) => {
                    if let Err(e) = dispatcherchannel.send(Message::StartedJob {
                        id: self.id,
                        pid: child.id(),
                    }) {
                        eprintln!("ERROR: Dispatcher send failure on start: {}", e)
                    }
                    let result = child.wait_with_output().unwrap();
                    let output: String = if let Ok(s) = result.stdout.try_into() {
                        s
                    } else {
                        format!("Process stdout is invalid UTF-8!")
                    };
                    let error: String = if let Ok(s) = result.stderr.try_into() {
                        s
                    } else {
                        format!("Process stderr is invalid UTF-8!")
                    };
                    if let Err(e) = dispatcherchannel.send(Message::FinishJob {
                        id: self.id,
                        exitstatus: result.status,
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
        });
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

#[derive(Clone, Debug, Hash, PartialEq, PartialOrd, Eq)]
pub(crate) struct ProjectKey {
    pub(crate) endpoint: usize,
    pub(crate) user: String,
    pub(crate) project: String,
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

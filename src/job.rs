use crate::config::EndPoint;
use crate::dispatcher::Message;
use crate::state::ServiceState;
use axum::http::HeaderMap;
use core::usize;
use derive_getters::Getters;
use std::sync::mpsc::Sender;

pub type JobId = usize;

#[derive(Debug, Clone, Getters)]
pub struct Job {
    /// Job identifier
    id: JobId,

    /// The particular endpoint in the service configuration this job is associated with (by index)
    endpoint_index: usize,

    /// The particular project this job is associated with (if any)
    project: Option<String>,

    /// The particular user this job is associated with (may be 'anonymous')
    user: String,

    // command
    command: String,
    args: Vec<String>,
}

impl Job {
    pub fn new(
        state: &ServiceState,
        endpoint_index: usize,
        project: Option<String>,
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
            user: user.into(),
            command: endpoint.command().into(),
            args,
        }
    }

    /// Spawns the job (consumes it)
    /// This spawns a lightweight monitoring thread (native thread) which in turn spawns a child process
    pub fn spawn(self, dispatcherchannel: Sender<Message>) {
        std::thread::spawn(move || {
            match std::process::Command::new(self.command)
                .args(self.args)
                .output()
            {
                Ok(result) => {
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
                    dispatcherchannel.send(Message::FinishJob {
                        id: self.id,
                        exitstatus: result.status,
                        output,
                        error,
                    });
                }
                Err(e) => {
                    dispatcherchannel.send(Message::FailStartJob {
                        id: self.id,
                        error: format!("{}", e),
                    });
                }
            }
        });
    }
}

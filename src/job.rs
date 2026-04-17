use crate::dispatcher::Message;
use derive_getters::Getters;
use std::sync::mpsc::Sender;

pub type JobId = usize;

#[derive(Debug, Clone, Getters)]
pub struct Job {
    /// Job identifier
    id: JobId,

    /// The particular endpoint in the service configuration this job is associated with (by index)
    endpoint: usize,

    /// The particular project this job is associated with (if any)
    project: Option<String>,

    /// The particular user this job is associated with (may be 'anonymous')
    user: String,

    // command
    command: String,
    args: Vec<String>,
}

impl Job {
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

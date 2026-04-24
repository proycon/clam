use crate::config::{DispatcherConfig, ServiceConfig};
use crate::job::{Job, JobId};
use crate::state::ServiceState;
use std::process::ExitStatus;
use std::sync::Arc;
use std::sync::mpsc::{Receiver, Sender};

/// The dispatcher is CLAM's job manager
/// It spawns jobs, in parallel, and monitors their execution
/// It also handles project creation/deletion
pub struct Dispatcher {
    state: Arc<ServiceState>,
    receiver: Receiver<Message>,
}

#[derive(Debug)]
pub enum Message {
    /// Submit a job to the queue
    SubmitJob(Job, Sender<ResponseMessage>),

    /// Forcibly stop a job, by job ID, discarding its results
    CancelJob(JobId, Sender<ResponseMessage>),

    /// Finish a job, this is sent by a job monitor thread to the dispatcher
    FinishJob {
        id: JobId,
        exitstatus: ExitStatus,
        /// stdout
        output: String,
        /// stderr
        error: String,
    },

    /// Fail a job, this is sent by a job monitor thread to the dispatcher
    FailStartJob { id: JobId, error: String },

    /// Poll job status
    PollJob(JobId, Sender<ResponseMessage>),

    /// Checks the queue for new jobs and spawns them, will be send after SubmitJob
    StartJobs,
}

#[derive(Debug)]
pub enum ResponseMessage {
    JobSubmitted,
    JobStopped,
    JobFinished {
        id: JobId,
        exitstatus: ExitStatus,
        /// stdout
        output: String,
        /// stderr
        error: String,
    },
    JobStarted,
    // A job failed to start
    JobStartFailed {
        error: String,
    },
}

impl Dispatcher {
    pub fn new(config: ServiceConfig) -> Self {
        let (sender, receiver) = std::sync::mpsc::channel();
        Self {
            state: Arc::new(ServiceState::new(config, sender)),
            receiver: receiver,
        }
    }

    pub fn state(&self) -> Arc<ServiceState> {
        self.state.clone()
    }

    /// Non-blocking function that spawns a new thread for the dispatcher
    pub fn spawn(self) {
        std::thread::spawn(move || {
            loop {
                // there should be no long-running blocking tasks in this loop!
                match self.receiver.recv() {
                    Ok(Message::SubmitJob(job, responsechannel)) => {
                        if let Ok(mut jobs) = self.state.pending_jobs.write() {
                            jobs.push_back(job);
                            let _ = responsechannel.send(ResponseMessage::JobSubmitted);
                            self.send(Message::StartJobs);
                        } else {
                            panic!("running job lock poisoned!");
                        }
                    }
                    Ok(Message::CancelJob(job_id, responsechannel)) => {
                        todo!();
                    }
                    Ok(Message::StartJobs) => self.start_jobs(),
                    Ok(Message::PollJob(job_id, responsechannel)) => {
                        todo!();
                    }
                    Ok(Message::FinishJob {
                        id,
                        exitstatus,
                        output,
                        error,
                    }) => {
                        todo!();
                    }
                    Ok(Message::FailStartJob { id, error }) => {
                        if let (Ok(mut running_jobs), Ok(mut done_jobs)) = (
                            self.state.running_jobs.write(),
                            self.state.done_jobs.write(),
                        ) {
                            if let Some(job) = running_jobs.remove(&id) {
                                done_jobs.insert(id, job);
                            } else {
                                eprintln!("Warning: Job not found: {}", id);
                            }
                        }
                    }
                    Err(e) => {
                        eprintln!("Corresponding sender died: {:?}", e);
                        break;
                    }
                }
            }
        });
    }

    pub fn send(&self, message: Message) {
        if let Ok(sender) = self.state.sender.read() {
            sender.send(message);
        }
    }

    pub fn start_jobs(&self) {
        loop {
            let running_job_count = if let Ok(running_jobs) = self.state.running_jobs.read() {
                running_jobs.len()
            } else {
                panic!("running job lock poisoned!");
            };

            if running_job_count < self.state().config.dispatcher().max_running_jobs() {
                let have_pending_jobs = if let Ok(pending_jobs) = self.state.pending_jobs.read() {
                    !pending_jobs.is_empty()
                } else {
                    panic!("pending job lock poisoned!")
                };

                if have_pending_jobs {
                    if let (Ok(mut running_jobs), Ok(mut pending_jobs), Ok(dispatcherchannel)) = (
                        self.state.running_jobs.write(),
                        self.state.pending_jobs.write(),
                        self.state.sender.read(),
                    ) {
                        if let Some(job) = pending_jobs.pop_front() {
                            //run the job in a monitoring thread
                            job.clone().spawn(dispatcherchannel.clone()); //the sender sends back to the dispatcher channel
                            // even if a job fails to start, it's temporarily added to running_jobs, the cleanup happens when handling Message::FailStartJob
                            running_jobs.insert(*job.id(), job);
                        }
                    }
                }
            }
        }
    }
}

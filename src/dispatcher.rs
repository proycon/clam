use crate::BackgroundServiceState;
use crate::config::ServiceConfig;
use crate::job::{Job, JobId, JobMaster};
use crate::project::ProjectKey;
use crate::state::ServiceState;
use std::process::ExitStatus;
use std::sync::Arc;
use std::sync::mpsc::Receiver;
use std::time::{SystemTime, UNIX_EPOCH};
use tokio::sync::oneshot;
use tracing::{debug, error};

/// The dispatcher is CLAM's job manager
/// It spawns jobs, in parallel, and monitors their execution
/// It also handles project creation/deletion
pub struct Dispatcher {
    state: Arc<ServiceState>,
    receiver: Receiver<Message>,
}

#[derive(Debug)]
/// A message to the dispatcher (by a service or by the dispatcher to itself)
pub enum Message {
    /// Submit a job to the queue
    SubmitJob(Job, oneshot::Sender<ResponseMessage>),

    /// Forcibly stop a job, by job ID, discarding its results
    CancelJob(JobId, oneshot::Sender<ResponseMessage>),

    StartedJob {
        id: JobId,
        pid: u32,
    },

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
    FailStartJob {
        id: JobId,
        error: String,
    },

    /// Status message (matching a specific stderr pattern)
    StatusLog(JobId, String),

    /// This message indicates that a background service is done loading and ready to be used
    Up(JobId),

    /// Poll job status
    PollJob(JobId, oneshot::Sender<ResponseMessage>),

    /// Checks the queue for new jobs and spawns them, will be send after SubmitJob
    StartJobs,
}

#[derive(Debug)]
pub enum ResponseMessage {
    JobSubmitted,
    JobStopped,
    JobFinished {
        id: JobId,
        exitstatus: i32,
        /// stdout
        output: String,
        /// stderr
        error: String,
    },
    // Job is running, encapsulating the job so status can be extracted
    JobRunning(Job),
    // Job is pending execution
    JobPending,
    JobStarted,
    // For example when a job failed to start
    JobError(String),
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

    pub fn associate_project_with_job(
        &self,
        projectkey: ProjectKey,
        job: &Job,
    ) -> Result<(), &'static str> {
        // this job is for a project, add it the project map
        if let Ok(mut project_job_map) = self.state.project_job_map.write() {
            // check if a job is already associated, don't allow running two jobs for the same project and user combination
            if let Some(job_id) = project_job_map.get(&projectkey) {
                let mut already_exists = false;
                if let Ok(jobs) = self.state.running_jobs.read() {
                    if jobs.contains_key(&job_id) {
                        already_exists = true;
                    }
                }
                if let Ok(jobs) = self.state.pending_jobs.read() {
                    if jobs.iter().any(|j| j.id() == job_id) {
                        already_exists = true;
                    }
                }
                if already_exists {
                    return Err(
                        "A job is already running for this project, refusing to start another one!",
                    );
                }
            }
            project_job_map.insert(projectkey, *job.id());
            Ok(())
        } else {
            panic!("project map poisoned");
        }
    }

    pub fn associate_background_service_with_job(
        &self,
        index: usize,
        job: &Job,
    ) -> Result<(), String> {
        if let Ok(mut bgservicestate_map) = self.state.bgservicestate_map.write() {
            match bgservicestate_map.get(index) {
                Some(BackgroundServiceState::Down)
                | Some(BackgroundServiceState::Failed { .. }) => {
                    bgservicestate_map[index] = BackgroundServiceState::Loading {
                        start_time: SystemTime::now()
                            .duration_since(UNIX_EPOCH)
                            .unwrap()
                            .as_secs() as usize,
                        job: *job.id(),
                    }
                }
                Some(BackgroundServiceState::Up { .. })
                | Some(BackgroundServiceState::Loading { .. }) => {
                    return Err(format!(
                        "Background service #{} already up or loading, refusing to start twice!",
                        index + 1
                    ));
                }
                None => unreachable!("No such background service"),
            }
            Ok(())
        } else {
            panic!("bgservice map poisoned");
        }
    }

    /// Non-blocking function that spawns a new thread for the dispatcher
    pub fn spawn(self) {
        tokio::task::spawn_blocking(move || {
            loop {
                // there should be no long-running blocking tasks in this loop!
                match self.receiver.recv() {
                    Ok(Message::SubmitJob(job, responsechannel)) => {
                        if let Some(projectkey) = job.projectkey() {
                            // this job is for a project, register the association
                            if let Err(e) = self.associate_project_with_job(projectkey, &job) {
                                let _ = responsechannel.send(ResponseMessage::JobError(e.into()));
                                continue;
                            }
                        } else if let JobMaster::BackgroundService(index) = job.master() {
                            // this job is for a background service, register the association
                            if let Err(e) = self.associate_background_service_with_job(*index, &job)
                            {
                                let _ = responsechannel.send(ResponseMessage::JobError(e));
                                continue;
                            }
                        }

                        //Note: it it not the task of the dispatcher at this point to schedule background services, that is the task of the caller that sent SubmitJob

                        // add job to pending jobs
                        if let Ok(mut jobs) = self.state.pending_jobs.write() {
                            debug!("job {} submitted", job.id());
                            jobs.push_back(job);
                            let _ = responsechannel.send(ResponseMessage::JobSubmitted);
                            self.send(Message::StartJobs);
                        } else {
                            panic!("running job lock poisoned!");
                        }
                    }
                    Ok(Message::CancelJob(job_id, responsechannel)) => {
                        //we only send the kill signal here, the actual cleanup will be picked up by FinishJob
                        if let Ok(jobs) = self.state.running_jobs.read() {
                            if let Some(job) = jobs.get(&job_id) {
                                debug!("cancelling job {:?}", job);
                                job.kill();
                            } else {
                                let _ = responsechannel.send(ResponseMessage::JobError(
                                    "No such job running".to_string(),
                                ));
                            }
                        }
                    }
                    Ok(Message::StartJobs) => self.start_jobs(),
                    Ok(Message::StartedJob { id, pid }) => {
                        if let Ok(mut jobs) = self.state.running_jobs.write() {
                            if let Some(job) = jobs.get_mut(&id) {
                                job.set_pid(pid);

                                //this is a background service, update itds state
                                if let JobMaster::BackgroundService(index) = job.master() {
                                    let bgservice = self.state.background_service(*index);
                                    if bgservice.up_pattern().is_none() {
                                        //background service does not define an output cue we can use to determine it's ready, so we consider it ready now it's been started
                                        if let Ok(mut bgservicestate_map) =
                                            self.state.bgservicestate_map.write()
                                        {
                                            bgservicestate_map[*index] =
                                                BackgroundServiceState::Up {
                                                    last_used_time: SystemTime::now()
                                                        .duration_since(UNIX_EPOCH)
                                                        .unwrap()
                                                        .as_secs()
                                                        as usize,
                                                    job: *job.id(),
                                                }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    Ok(Message::PollJob(job_id, responsechannel)) => {
                        debug!("polling job {:?}", job_id);
                        if let (Ok(running_jobs), Ok(done_jobs)) =
                            (self.state.running_jobs.read(), self.state.done_jobs.read())
                        {
                            if let Some(job) = running_jobs.get(&job_id) {
                                let _ =
                                    responsechannel.send(ResponseMessage::JobRunning(job.clone()));
                            } else if let Some(job) = done_jobs.get(&job_id) {
                                if let Some(exitstatus) = job.exitstatus() {
                                    let _ = responsechannel.send(ResponseMessage::JobFinished {
                                        id: *job.id(),
                                        exitstatus: *exitstatus,
                                        output: job.output().as_ref().cloned().unwrap_or_default(),
                                        error: job.error().as_ref().cloned().unwrap_or_default(),
                                    });
                                } else {
                                    let _ =
                                        responsechannel.send(ResponseMessage::JobError(format!(
                                            "Job failed to start: {}",
                                            job.error().as_deref().unwrap_or_default()
                                        )));
                                }
                            } else {
                                let mut pending = false;
                                if let Ok(pending_jobs) = self.state.pending_jobs.read() {
                                    //MAYBE TODO: this scales poorly to huge numbers of pending jobs
                                    for pending_job in pending_jobs.iter() {
                                        if *pending_job.id() == job_id {
                                            pending = true;
                                            break;
                                        }
                                    }
                                }
                                if pending {
                                    let _ = responsechannel.send(ResponseMessage::JobPending);
                                } else {
                                    let _ = responsechannel.send(ResponseMessage::JobError(
                                        "No such job found".to_string(),
                                    ));
                                }
                            }
                        }
                    }
                    Ok(Message::FinishJob {
                        id,
                        exitstatus,
                        output,
                        error,
                    }) => {
                        if let (Ok(mut running_jobs), Ok(mut done_jobs)) = (
                            self.state.running_jobs.write(),
                            self.state.done_jobs.write(),
                        ) {
                            if let Some(mut job) = running_jobs.remove(&id) {
                                debug!("finishing job {:?}", job);
                                job.set_output(output);
                                job.set_error(error);
                                if let Some(code) = exitstatus.code() {
                                    job.set_exitstatus(code);
                                }
                                done_jobs.insert(id, job);
                            } else {
                                eprintln!("Warning: Job not found: {}", id);
                            }
                        }
                    }
                    Ok(Message::FailStartJob { id, error }) => {
                        if let (Ok(mut running_jobs), Ok(mut done_jobs)) = (
                            self.state.running_jobs.write(),
                            self.state.done_jobs.write(),
                        ) {
                            if let Some(mut job) = running_jobs.remove(&id) {
                                debug!("failed to start job {:?}: {}", job, error);
                                job.set_error(error);
                                done_jobs.insert(id, job);
                            } else {
                                eprintln!("Warning: Job not found: {}", id);
                            }
                        }
                    }
                    Ok(Message::StatusLog(job_id, message)) => {
                        if let Ok(mut running_jobs) = self.state.running_jobs.write() {
                            running_jobs.entry(job_id).and_modify(|job| {
                                job.log(message.as_str());

                                // convert any mentioned percentage into a progress number (0-100)
                                if let Some(progress_pattern) =
                                    self.state.config().progress_pattern()
                                {
                                    for (_, [percentage]) in progress_pattern
                                        .captures_iter(message.as_str())
                                        .map(|c| c.extract())
                                    {
                                        if let Ok(progress) = percentage.parse() {
                                            job.set_progress(progress);
                                        }
                                    }
                                }
                            });
                        }
                        //MAYBE TODO: also check done_jobs in case of race conditions?
                    }
                    Ok(Message::Up(job_id)) => {
                        //job is a background service that has finished loading and now up and ready to receive connections
                        //we adapt the background service state in the map
                        if let Ok(mut running_jobs) = self.state.running_jobs.write() {
                            running_jobs.entry(job_id).and_modify(|job| {
                                job.mark_ready(); //this ensures we only receive this signal once
                                if let JobMaster::BackgroundService(index) = job.master() {
                                    //mark the entire background service as up
                                    if let Ok(mut bgservicestate_map) =
                                        self.state.bgservicestate_map.write()
                                    {
                                        bgservicestate_map[*index] = BackgroundServiceState::Up {
                                            last_used_time: SystemTime::now()
                                                .duration_since(UNIX_EPOCH)
                                                .unwrap()
                                                .as_secs()
                                                as usize,
                                            job: *job.id(),
                                        }
                                    }
                                }
                            });
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
            if let Err(e) = sender.send(message) {
                eprintln!("ERROR: Dispatcher send failed: {}", e)
            }
        }
    }

    // start all pendings jobs (if any, and up until a maximum of running jobs)
    // there should be no long-running blocking tasks in this loop!
    pub fn start_jobs(&self) {
        let mut postpone_jobs = Vec::new(); //holds jobs that will be postponed until next call (e.g. because they are waiting for background services)
        loop {
            let running_job_count = if let Ok(running_jobs) = self.state.running_jobs.read() {
                running_jobs.len()
            } else {
                panic!("running job lock poisoned!");
            };
            debug!(
                "start_jobs: {}/{} jobs running",
                running_job_count,
                self.state().config.dispatcher().max_running_jobs()
            );

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
                            if self.background_services_up(&job) {
                                //run the job in a monitoring thread
                                debug!("start_jobs: starting job {:?}", job);
                                job.clone().spawn(dispatcherchannel.clone()); //the sender sends back to the dispatcher channel, we discard the joinhandle, the process will be *detached*
                                // even if a job fails to start, it's temporarily added to running_jobs, the cleanup happens when handling Message::FailStartJob
                                running_jobs.insert(*job.id(), job);
                            } else {
                                postpone_jobs.push(job);
                            }
                        }
                    }
                } else {
                    //no jobs left
                    break;
                }
            } else {
                //maximum reached... TODO: start_jobs will have to be retriggered periodically to give the queue a chance to clear!!
                break;
            }
        }

        //add postponed jobs back to the front of the queue
        if !postpone_jobs.is_empty() {
            if let Ok(mut pending_jobs) = self.state.pending_jobs.write() {
                postpone_jobs.reverse();
                for job in postpone_jobs {
                    pending_jobs.push_front(job);
                }
            }
        }
    }

    /// Checks whether all background service dependencies are up, and if so, updates their last used timestamp.
    /// If there are no background services, this always returns true immediately.
    pub fn background_services_up(&self, job: &Job) -> bool {
        if job.background_services().is_empty() {
            //bail out early and cheaply if we don't rely on any background services
            return true;
        }
        if let Ok(mut bgservicestate_map) = self.state.bgservicestate_map.write() {
            for bgservice_index in job.background_services().iter() {
                if let Some(BackgroundServiceState::Up { last_used_time, .. }) =
                    bgservicestate_map.get_mut(*bgservice_index)
                {
                    *last_used_time = SystemTime::now()
                        .duration_since(UNIX_EPOCH)
                        .unwrap()
                        .as_secs() as usize;
                } else {
                    return false;
                }
            }
        } else {
            panic!("bgservicestate_map lock poisoned");
        }
        true
    }

    /// Checks whether a background service is up, and if so, updates its last used timestamp
    pub fn background_service_up(&self, bgservice_index: usize) -> bool {
        if let Ok(mut bgservicestate_map) = self.state.bgservicestate_map.write() {
            if let Some(BackgroundServiceState::Up { last_used_time, .. }) =
                bgservicestate_map.get_mut(bgservice_index)
            {
                *last_used_time = SystemTime::now()
                    .duration_since(UNIX_EPOCH)
                    .unwrap()
                    .as_secs() as usize;
                true
            } else {
                false
            }
        } else {
            panic!("bgservicestate_map lock poisoned");
        }
    }
}

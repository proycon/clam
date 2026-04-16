use std::path::PathBuf;

#[derive(Copy, Clone, Debug)]
pub enum JobState {
    /// The job is waiting in the queue to be picked up by the dispatcher
    Pending,

    /// The job is running
    Running,

    /// The job is done
    Done { exitcode: usize },
}

#[derive(Debug)]
pub struct Job {
    /// Job identifier
    id: String,

    /// The particular endpoint in the service configuration this job is associated with (by index)
    endpoint: usize,

    /// The particular project this job is associated with (if any)
    project: Option<String>,

    /// The particular user this job is associated with (None = anonymous)
    user: Option<String>,
}

pub struct Share {
    path: PathBuf,
    onetime: bool,
}

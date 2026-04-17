use crate::dispatcher::Message;
use crate::job::{Job, JobId};
use core::default::Default;
use std::collections::{HashMap, HashSet, VecDeque};
use std::path::PathBuf;
use std::sync::RwLock;
use std::sync::mpsc::Sender;

pub struct Share {
    path: PathBuf,
    onetime: bool,
}

pub(crate) struct ServiceState {
    /// Jobs
    pub(crate) pending_jobs: RwLock<VecDeque<Job>>,
    pub(crate) running_jobs: RwLock<HashMap<JobId, Job>>,
    pub(crate) done_jobs: RwLock<HashMap<JobId, Job>>,

    /// Map of users to projects
    pub(crate) user_project_map: RwLock<HashMap<String, HashSet<String>>>,

    /// Public non-discoverable shared files (bypasses authentication)
    pub(crate) shares: RwLock<HashMap<String, Share>>,

    /// Map of usernames to hashed passwords
    pub(crate) user_db: RwLock<HashMap<String, String>>,

    pub(crate) sender: RwLock<Sender<Message>>,
}

impl ServiceState {
    pub fn new(sender: Sender<Message>) -> Self {
        Self {
            sender: RwLock::new(sender),
            pending_jobs: RwLock::new(Default::default()),
            running_jobs: RwLock::new(Default::default()),
            done_jobs: RwLock::new(Default::default()),
            user_project_map: RwLock::new(Default::default()),
            shares: RwLock::new(Default::default()),
            user_db: RwLock::new(Default::default()),
        }
    }
}

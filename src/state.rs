use crate::config::{EndPoint, OAuth2Config, ServiceConfig};
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

    /// Map of usernames to hashed passwords (loaded from external file)
    pub(crate) user_db: RwLock<HashMap<String, String>>,

    /// Oauth2 credentials (loaded from external file)
    pub(crate) oauth2config: RwLock<OAuth2Config>,

    pub(crate) sender: RwLock<Sender<Message>>,

    pub(crate) config: ServiceConfig,
}

fn read_user_db(config: &ServiceConfig) -> Result<HashMap<String, String>, std::io::Error> {
    let mut user_db: HashMap<String, String> = HashMap::new();
    if let Some(user_file) = config.auth().user_file() {
        let f = std::fs::File::open(user_file)?;
        let reader = std::io::BufReader::new(f);
        for line in std::io::BufRead::lines(reader) {
            let line = line.unwrap();
            let parts: Vec<&str> = line.split('\t').collect();
            if parts.len() >= 2 {
                let username = parts[0];
                let password_hash = parts[1];
                user_db.insert(username.to_string(), password_hash.to_string());
            }
        }
    }
    Ok(user_db)
}

fn read_oauth_config(config: &ServiceConfig) -> Result<OAuth2Config, String> {
    if let Some(filename) = config.auth().oauth_config_file() {
        let data = std::fs::read_to_string(filename)
            .map_err(|e| format!("Failed to read OAuth config file: {}", e))?;
        let oauth2_config: OAuth2Config = serde_json::from_str(&data)
            .map_err(|e| format!("Failed to parse OAuth config: {}", e))?;
        Ok(oauth2_config)
    } else {
        Ok(Default::default())
    }
}

impl ServiceState {
    pub fn new(config: ServiceConfig, sender: Sender<Message>) -> Self {
        Self {
            sender: RwLock::new(sender),
            pending_jobs: RwLock::new(Default::default()),
            running_jobs: RwLock::new(Default::default()),
            done_jobs: RwLock::new(Default::default()),
            user_project_map: RwLock::new(Default::default()),
            shares: RwLock::new(Default::default()),
            user_db: RwLock::new(read_user_db(&config).expect(&format!(
                "User database could not be read from {}",
                config.auth().user_file().as_deref().unwrap()
            ))),
            oauth2config: RwLock::new(read_oauth_config(&config).expect(&format!(
                "Oauth2 config could not be read from {}",
                config.auth().oauth_config_file().as_deref().unwrap()
            ))),
            config,
        }
    }

    pub fn config(&self) -> &ServiceConfig {
        &self.config
    }

    /// Send a message to the dispatcher
    pub fn send(&self, message: Message) {
        if let Ok(sender) = self.sender.read() {
            sender.send(message);
        }
    }

    /// Retrieve an endpoint by index, will panic if it does not exist!
    pub fn endpoint(&self, endpoint_index: usize) -> &EndPoint {
        self.config()
            .endpoints()
            .get(endpoint_index)
            .expect("endpoint must exist")
    }
}

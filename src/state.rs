use crate::auth::{OpenIdConfiguration, get_jwks, get_openid_config};
use crate::config::{EndPoint, OAuthCredentials, ServiceConfig};
use crate::dispatcher::Message;
use crate::job::{Job, JobId};
use core::default::Default;
use jsonwebtoken::jwk::JwkSet;
use std::collections::{HashMap, HashSet, VecDeque};
use std::path::PathBuf;
use std::sync::Arc;
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
    pub(crate) oauthcredentials: OAuthCredentials,

    /// OpenID configuration as obtained from .well-know/openid-configuration endpoint
    pub(crate) openidconfig: Option<OpenIdConfiguration>,

    pub(crate) sender: RwLock<Sender<Message>>,

    pub(crate) config: ServiceConfig,

    /// JSON Web Key Set to efficiently validate tokens (it should never be fetched on each request, but fetched and cached as otherwise it is inefficient)
    pub(crate) jwkset: Option<JwkSet>,
}

/// Parse the user database, a simple TSV file with a username, a tab and a hashed password on each line
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

/// Read the OAuth config with the openid credentials and the configuration endpoint
fn read_oauth_config(config: &ServiceConfig) -> Result<OAuthCredentials, String> {
    if let Some(filename) = config.auth().oauth_config_file() {
        let data = std::fs::read_to_string(filename)
            .map_err(|e| format!("Failed to read OAuth config file: {}", e))?;
        let oauth2_config: OAuthCredentials = serde_json::from_str(&data)
            .map_err(|e| format!("Failed to parse OAuth config file: {}", e))?;
        Ok(oauth2_config)
    } else {
        Ok(Default::default())
    }
}

impl ServiceState {
    pub fn new(config: ServiceConfig, sender: Sender<Message>) -> Self {
        //read oauth credentials and metadata endpoint
        let oauthcredentials = read_oauth_config(&config).expect("Unable to read oauth config");
        // get configuration from metadata endpoint
        let openidconfig = if oauthcredentials.enabled() {
            Some(get_openid_config(
                &oauthcredentials.openid_configuration_url,
            ))
        } else {
            None
        };

        // get JSON Web Token Set for OIDC
        let jwkset = if let Some(openidconfig) = openidconfig.as_ref() {
            Some(get_jwks(openidconfig.jwks_uri.as_str()))
        } else {
            None
        };

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
            oauthcredentials,
            openidconfig,
            jwkset,
            config,
        }
    }

    pub fn config(&self) -> &ServiceConfig {
        &self.config
    }

    /// Send a message to the dispatcher
    pub fn send(&self, message: Message) {
        if let Ok(sender) = self.sender.read() {
            if let Err(e) = sender.send(message) {
                eprintln!("ERROR: State send failed: {}", e)
            }
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

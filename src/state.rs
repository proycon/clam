use crate::auth::{OpenIdConfiguration, get_jwks, get_openid_config};
use crate::config::{EndPoint, OAuthCredentials, ServiceConfig};
use crate::dispatcher::Message;
use crate::job::{Job, JobId};
use crate::templating::init_templating;
use core::default::Default;
use jsonwebtoken::jwk::JwkSet;
use std::collections::{HashMap, VecDeque};
use std::path::PathBuf;
use std::sync::RwLock;
use std::sync::mpsc::Sender;
use tracing::debug;

use crate::project::{Project, ProjectKey, ProjectStatus};

// TODO: implement shares
pub struct Share {
    path: PathBuf,
    onetime: bool,
}

pub struct ServiceState {
    /// Jobs
    pub(crate) pending_jobs: RwLock<VecDeque<Job>>,
    pub(crate) running_jobs: RwLock<HashMap<JobId, Job>>,
    pub(crate) done_jobs: RwLock<HashMap<JobId, Job>>,

    /// Maps projects (pertaining to users and endpoints) to jobs, facilitates quick lookup of project status
    pub(crate) project_job_map: RwLock<HashMap<ProjectKey, JobId>>,

    /// Public non-discoverable shared files (bypasses authentication)
    pub(crate) shares: RwLock<HashMap<String, Share>>,

    /// Map of usernames to hashed passwords (loaded from external file)
    pub(crate) user_db: RwLock<HashMap<String, String>>,

    /// Oauth2 credentials (loaded from external file)
    pub(crate) oauthcredentials: OAuthCredentials,

    /// OpenID configuration as obtained from .well-know/openid-configuration endpoint
    pub(crate) openidconfig: Option<OpenIdConfiguration>,

    pub(crate) sender: RwLock<Sender<Message>>,

    /// Service Configuration
    pub(crate) config: ServiceConfig,

    /// API specific in OpenAPI format
    pub(crate) openapi: utoipa::openapi::OpenApi,

    /// JSON Web Key Set to efficiently validate tokens (it should never be fetched on each request, but fetched and cached as otherwise it is inefficient)
    pub(crate) jwkset: Option<JwkSet>,

    pub(crate) templating: Option<upon::Engine<'static>>,
    pub(crate) template_context: Option<upon::Value>,
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
            project_job_map: RwLock::new(Default::default()),
            shares: RwLock::new(Default::default()),
            user_db: RwLock::new(if let Some(user_file) = config.auth().user_file() {
                read_user_db(&config).expect(&format!(
                    "User database could not be read from {}",
                    user_file
                ))
            } else {
                HashMap::new()
            }),
            oauthcredentials,
            openidconfig,
            openapi: (&config).into(), //compute and associate openAPI specification
            jwkset,
            templating: if config.disable_ui() {
                None
            } else {
                Some(init_templating())
            },
            template_context: if config.disable_ui() {
                None
            } else {
                let config: upon::Value = (&config).into();
                Some(upon::value! { config: config })
            },
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

    /// Returns the project status, or None if it does not exist yet
    pub fn project_status(&self, project: &Project<'_>) -> Option<ProjectStatus> {
        if !project.exists() {
            return None;
        }

        //gather associated job (if any)
        let job_id = if let Ok(project_job_map) = self.project_job_map.read() {
            project_job_map.get(project.key()).map(|x| x.clone())
        } else {
            return Some(ProjectStatus::Staging {
                input_files: project.input_files(),
            });
        };

        if let Some(job_id) = job_id {
            if let Ok(running_jobs) = self.running_jobs.read() {
                if let Some(job) = running_jobs.get(&job_id) {
                    return Some(ProjectStatus::Running {
                        progress: job.progress().clone(),
                        statuslog: job.statuslog().clone(),
                    });
                }
            }

            if let Ok(done_jobs) = self.done_jobs.read() {
                if let Some(job) = done_jobs.get(&job_id) {
                    return Some(ProjectStatus::Done {
                        success: job.exitstatus() == &Some(0),
                        statuslog: Some(job.statuslog().clone()),
                        input_files: project.input_files(),
                        output_files: project.output_files(),
                    });
                }
            }

            if let Ok(pending_jobs) = self.pending_jobs.read() {
                //MAYBE TODO: this scales poorly to huge numbers of pending jobs
                for pending_job in pending_jobs.iter() {
                    if *pending_job.id() == job_id {
                        return Some(ProjectStatus::Scheduled);
                    }
                }
            }
        }

        Some(ProjectStatus::Staging {
            input_files: project.input_files(),
        })
    }
}

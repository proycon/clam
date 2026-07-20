mod auth;
mod config;
mod dispatcher;
mod error;
mod job;
mod openapi;
mod project;
mod service;
mod state;
pub use auth::*;
pub use config::*;
pub use dispatcher::*;
pub use error::*;
pub use service::*;
pub use state::*;

use const_format::concatcp;

pub const VERSION: &str = env!("CARGO_PKG_VERSION");
pub const SERVER: &str = concatcp!("clam/", VERSION);

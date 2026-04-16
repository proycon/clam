use crate::config::{EndPoint, ServiceConfig};
use crate::job::Job;
use std::path::PathBuf;
use tokio::signal;
use tower_http::trace::TraceLayer;

use axum::Router;
use std::collections::HashMap;
use std::collections::VecDeque;
use std::sync::Arc;

pub struct Service {
    config: ServiceConfig,
    state: Arc<ServiceState>,
}

#[derive(Default)]
struct ServiceState {
    /// Jobs
    jobs: VecDeque<Job>,

    /// Public non-discoverable shared files (bypasses authentication)
    shares: HashMap<String, Share>,

    /// Map of usernames to hashed passwords
    user_db: HashMap<String, String>,
}

impl Service {
    pub fn new(config: ServiceConfig) -> Self {
        let state = ServiceState::default().into();
        Self { config, state }
    }

    #[tokio::main]
    pub async fn run(&self) {
        let bind = self.config.listen().as_deref().unwrap_or("127.0.0.1:8080");
        eprintln!("[clamservice] listening on {}", bind);
        let listener = tokio::net::TcpListener::bind(bind).await.unwrap();

        let mut router: Router = Router::new().with_state(self.state.clone());
        //TODO: add endpoints
        for endpoint in self.config.endpoints().iter() {
            router = self.configure_endpoint(router, endpoint);
        }
        router = router
            //.merge(SwaggerUi::new("/swagger-ui").url("/api-doc/openapi.json", ApiDoc::openapi()))
            .layer(TraceLayer::new_for_http());

        axum::serve(listener, router)
            .with_graceful_shutdown(shutdown_signal(self.state.clone()))
            .await
            .unwrap();
    }

    pub fn configure_endpoint(&self, router: Router, endpoint: &EndPoint) -> Router {
        router.route(endpoint.path(), method_router)
    }
}

async fn shutdown_signal(state: Arc<ServiceState>) {
    let ctrl_c = async {
        signal::ctrl_c()
            .await
            .expect("failed to install Ctrl+C handler");
    };

    #[cfg(unix)]
    let terminate = async {
        signal::unix::signal(signal::unix::SignalKind::terminate())
            .expect("failed to install signal handler")
            .recv()
            .await;
    };

    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        _ = ctrl_c => {
        }
        _ = terminate => {
        }
    }
}

pub struct Share {
    path: PathBuf,
    onetime: bool,
}

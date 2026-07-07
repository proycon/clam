use crate::config::ServiceConfig;
use utoipa::openapi::{Components, Info, OpenApi, OpenApiBuilder, Paths};

impl From<&ServiceConfig> for OpenApi {
    fn from(config: &ServiceConfig) -> Self {
        let mut info = Info::new(config.name(), config.version());
        info.description = config.description().clone();

        let openapi = OpenApiBuilder::new()
            .info(info)
            .paths(Paths::new())
            .components(Some(Components::new()))
            .build();
        openapi
    }
}

use crate::config::ServiceConfig;
use upon::Engine;

// All templates are compiled in at build time

const TEMPLATE_HEADER: &str = include_str!(concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/templates/header.html"
));
const TEMPLATE_FOOTER: &str = include_str!(concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/templates/footer.html"
));
const TEMPLATE_LANDING: &str = include_str!(concat!(
    env!("CARGO_MANIFEST_DIR"),
    "/templates/landingpage.html"
));

pub(crate) fn init_templating() -> Engine<'static> {
    let mut engine = Engine::new();
    engine
        .add_template("header", TEMPLATE_HEADER)
        .expect("Failed to compile header template");
    engine
        .add_template("footer", TEMPLATE_FOOTER)
        .expect("Failed to compile footer template");
    engine
        .add_template("landingpage", TEMPLATE_LANDING)
        .expect("Failed to compile landing page template");
    engine.add_function("exists", |s: &str| !s.is_empty());
    engine
}

impl From<&ServiceConfig> for upon::Value {
    fn from(config: &ServiceConfig) -> Self {
        upon::value! {
            name: config.name().clone(),
            version: config.version().clone(),
            description: config.description().clone().unwrap_or_default(),
            authors: config.authors().clone(),
            documentation_url: config.documentation_url().clone().unwrap_or_default(),
            sourcerepo: config.documentation_url().clone().unwrap_or_default(),
            termsofservice: config.termsofservice().clone().unwrap_or_default(),
            contact_name: if let Some(contact) = config.contact() {
                contact.name.clone().unwrap_or_default()
            } else { String::new() },
            contact_email: if let Some(contact) = config.contact() {
                contact.email.clone().unwrap_or_default()
            } else { String::new() },
        }
    }
}

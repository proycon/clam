use crate::config::{EndPointMode, ServiceConfig};
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
    engine.add_function("join", |list: &upon::Value, delimiter: &str| match list {
        upon::Value::List(list) => {
            //too much cloning but it'll do for now
            let newlist: Vec<String> = list
                .iter()
                .map(|v| match v {
                    upon::Value::String(s) => s.clone(),
                    upon::Value::Integer(d) => format!("{}", d),
                    upon::Value::Float(d) => format!("{}", d),
                    upon::Value::Bool(d) => format!("{}", d),
                    _ => String::new(),
                })
                .collect();
            upon::Value::String(newlist.join(delimiter))
        }
        _ => {
            list.clone() //was not really a list after all, just pass it on so we don't need to panic
        }
    });
    engine
}

impl From<&ServiceConfig> for upon::Value {
    fn from(config: &ServiceConfig) -> Self {
        upon::value! {
            name: config.name().clone(),
            version: config.version().clone(),
            clam_version: env!("CARGO_PKG_VERSION"),
            description: config.description().clone().unwrap_or_default(),
            authors: config.authors().clone(),
            affiliation: config.affiliation().clone().unwrap_or_default(),
            documentation_url: config.documentation_url().clone().unwrap_or_default(),
            sourcerepo: config.documentation_url().clone().unwrap_or_default(),
            termsofservice: config.termsofservice().clone().unwrap_or_default(),
            contact_name: if let Some(contact) = config.contact() {
                contact.name.clone().unwrap_or_default()
            } else { String::new() },
            contact_email: if let Some(contact) = config.contact() {
                contact.email.clone().unwrap_or_default()
            } else { String::new() },
            endpoints: config.endpoints().iter().filter_map(|endpoint| {
                if endpoint.mode() == &EndPointMode::Action || endpoint.mode() == &EndPointMode::Project {
                    Some(upon::value! {
                        name: endpoint.name(),
                        path: endpoint.path(),
                        description: endpoint.description(),
                    })
                } else {
                    None
                }
            }).collect::<Vec<upon::Value>>()
        }
    }
}

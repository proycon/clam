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
        .add_template("landing", TEMPLATE_LANDING)
        .expect("Failed to compile landing page template");
    engine
}

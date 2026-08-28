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
const TEMPLATE_PORCH: &str =
    include_str!(concat!(env!("CARGO_MANIFEST_DIR"), "/templates/porch.html"));

pub(crate) fn init_templating() -> Engine<'static> {
    let mut engine = Engine::new();
    engine
        .add_template("header", TEMPLATE_HEADER)
        .expect("Failed to compile header template");
    engine
        .add_template("footer", TEMPLATE_FOOTER)
        .expect("Failed to compile footer template");
    engine
        .add_template("porch", TEMPLATE_PORCH)
        .expect("Failed to compile porch template");
    engine
}

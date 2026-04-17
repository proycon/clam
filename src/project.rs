use std::path::Path;

/// A project is a workspace for a user that holds input and output files
#[derive(Debug)]
pub struct Project {
    /// The identifier of the project
    id: String,

    user: String,

    endpoint: String,
}

impl Project {
    pub fn create(&self, rootdir: &Path) {}
}

/// A project is a workspace for a user that holds input and output files
pub struct Project {
    /// The identifier of the project
    id: String,

    user: Option<String>,
}

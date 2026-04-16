#[derive(Debug)]
pub enum ClamError {
    MissingEnvVariable(String),
    ConfigError(toml::de::Error),
    IoError(std::io::Error),
}

use clam::*;
use clap::Parser;

#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Args {
    /// Service configuration file (toml).
    #[arg(short, long)]
    config: String,
}

fn main() {
    let args = Args::parse();

    match if args.config == "-" {
        clam::ServiceConfig::from_stdin()
    } else {
        clam::ServiceConfig::from_file(args.config.as_str())
    } {
        Ok(config) => match config.validate() {
            Ok(()) => {
                let service = Service::new(config);
                service.run();
            }
            Err(ClamError::ConfigValidationError(e)) => {
                eprintln!("Error validating configuration: {}", e.to_string());
                std::process::exit(1);
            }
            Err(_) => unreachable!("only configvalidationerror expected"),
        },
        Err(ClamError::ConfigError(e)) => {
            eprintln!("Error parsing configuration: {}", e.to_string());
            std::process::exit(1);
        }
        Err(ClamError::IoError(e)) => {
            eprintln!("Error reading configuration: {}", e.to_string());
            std::process::exit(1);
        }
        Err(e) => {
            eprintln!("Error reading configuration: {:?}", e);
            std::process::exit(1);
        }
    }
}

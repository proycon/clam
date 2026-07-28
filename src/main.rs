use clam::*;
use clap::Parser;
use tracing::{error, info};

#[derive(Parser, Debug)]
#[command(version, about, long_about = None)]
struct Args {
    /// Service configuration file (toml).
    #[arg(short, long)]
    config: String,

    /// Debug mode, output verbose information
    #[arg(short, long)]
    debug: bool,

    /// Quiet mode, output as little as possible
    #[arg(short, long)]
    quiet: bool,

    #[arg(long)]
    /// Validate the configuration only, do not start the service
    check: bool,

    #[arg(long)]
    /// Disable the Web User interface
    disable_ui: bool,
}

fn main() {
    let args = Args::parse();

    if args.debug {
        tracing_subscriber::fmt()
            .with_max_level(tracing::Level::DEBUG)
            .init();
    } else if args.quiet {
        tracing_subscriber::fmt()
            .with_max_level(tracing::Level::WARN)
            .init();
    } else {
        tracing_subscriber::fmt()
            .with_max_level(tracing::Level::INFO)
            .init();
    }

    if args.disable_ui {
        info!("Web User Interface disabled from command line");
    }

    match if args.config == "-" {
        clam::ServiceConfig::from_stdin()
    } else {
        clam::ServiceConfig::from_file(args.config.as_str())
    } {
        Ok(mut config) => match config.validate() {
            Ok(()) => {
                if args.check {
                    std::process::exit(0);
                }
                if args.disable_ui {
                    config.set_disable_ui();
                }
                let service = Service::new(config);
                service.run();
            }
            Err(ClamError::ConfigValidationError(e)) => {
                error!("Error validating configuration: {}", e.to_string());
                std::process::exit(1);
            }
            Err(_) => unreachable!("only configvalidationerror expected"),
        },
        Err(ClamError::ConfigError(e)) => {
            error!("Error parsing configuration: {}", e.to_string());
            std::process::exit(1);
        }
        Err(ClamError::IoError(e)) => {
            error!("Error reading configuration: {}", e.to_string());
            std::process::exit(1);
        }
        Err(e) => {
            error!("Error reading configuration: {:?}", e);
            std::process::exit(1);
        }
    }
}

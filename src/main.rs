use clam::*;
use clap::Parser;

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

    match if args.config == "-" {
        clam::ServiceConfig::from_stdin()
    } else {
        clam::ServiceConfig::from_file(args.config.as_str())
    } {
        Ok(config) => match config.validate() {
            Ok(()) => {
                if args.check {
                    std::process::exit(0);
                }
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

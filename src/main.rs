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

    let config = if args.config == "-" {
        clam::ServiceConfig::from_stdin()
    } else {
        clam::ServiceConfig::from_file(args.config.as_str())
    }
    .expect("Error reading configuration");

    let service = Service::new(config);
    service.run();
}

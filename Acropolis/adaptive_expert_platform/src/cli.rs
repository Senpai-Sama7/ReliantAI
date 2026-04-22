//! Command-line interface definitions for the Adaptive Expert Platform.

use clap::{Parser, Subcommand};

#[derive(Parser, Debug)]
#[command(name = "adaptive-expert-platform")]
#[command(about = "A secure, polyglot AI orchestration platform", long_about = None)]
pub struct Cli {
    #[command(subcommand)]
    pub command: Commands,
}

#[derive(Subcommand, Debug)]
pub enum Commands {
    /// Start the server
    Serve {
        /// Address to bind to
        #[arg(short, long)]
        addr: Option<String>,
    },
    /// Run a batch processing job
    Run {
        /// Path to the batch configuration file
        #[arg(short, long)]
        config: String,
    },
    /// Initialize the first admin user
    InitAdmin {
        /// Username for the admin
        #[arg(short, long)]
        username: String,
        /// Password for the admin (prompts if not provided)
        #[arg(short, long)]
        password: Option<String>,
    },
}

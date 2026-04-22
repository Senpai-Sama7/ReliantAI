//! Main entry point for the Adaptive Expert Platform CLI.

use adaptive_expert_platform::{
    batch, cli, server, settings::Settings, telemetry,
    auth::AuthManager,
};
use anyhow::Result;
use clap::Parser;
use rpassword::read_password;

#[tokio::main]
async fn main() -> Result<()> {
    // Parse command line arguments
    let args = cli::Cli::parse();

    // Load settings
    let settings = Settings::load()?;

    // Initialize telemetry
    telemetry::init(settings.otlp_endpoint.as_deref())?;

    // Execute the requested command
    match args.command {
        cli::Commands::Serve { addr: _ } => {
            server::serve(&settings).await
        }
        cli::Commands::Run { config } => {
            batch::run(config.into(), settings).await
        }
        cli::Commands::InitAdmin { username, password } => {
            init_admin(username, password, &settings).await
        }
    }
}

/// Initialize the first admin user
async fn init_admin(username: String, password: Option<String>, settings: &Settings) -> Result<()> {
    // Validate JWT secret before proceeding
    validate_jwt_secret(settings)?;
    
    let db_path = settings.db_path.clone().unwrap_or_else(|| "./acropolis_db/auth".to_string());
    let jwt_secret = get_jwt_secret(settings)?;
    let auth_manager = AuthManager::new(jwt_secret, &db_path)?;
    
    // Check if admin already exists
    if auth_manager.has_admin()? {
        return Err(anyhow::anyhow!("Admin user already exists. Cannot reinitialize."));
    }
    
    let password = match password {
        Some(p) => p,
        None => {
            print!("Enter admin password: ");
            std::io::Write::flush(&mut std::io::stdout())?;
            read_password()?
        }
    };
    
    // Validate password strength
    if password.len() < 12 {
        return Err(anyhow::anyhow!("Password must be at least 12 characters long"));
    }
    
    auth_manager.initialize_admin(username, &password)?;
    println!("Admin user initialized successfully");
    Ok(())
}

/// Validate JWT secret meets security requirements
fn validate_jwt_secret(settings: &Settings) -> Result<()> {
    let jwt_secret = get_jwt_secret(settings)?;
    
    // Check minimum length
    if jwt_secret.len() < 32 {
        return Err(anyhow::anyhow!("JWT secret must be at least 32 characters long"));
    }
    
    // Check for default/weak secrets
    let weak_secrets = [
        "default_insecure_secret_change_in_production",
        "secret",
        "jwt_secret",
        "change_me",
        "insecure",
    ];
    
    if weak_secrets.contains(&jwt_secret.as_str()) {
        return Err(anyhow::anyhow!("JWT secret is using a known weak value. Please use a strong, random secret."));
    }
    
    // Basic entropy check - ensure it's not all the same character
    let unique_chars: std::collections::HashSet<char> = jwt_secret.chars().collect();
    if unique_chars.len() < 4 {
        return Err(anyhow::anyhow!("JWT secret lacks sufficient entropy. Use a random, complex secret."));
    }
    
    Ok(())
}

/// Get JWT secret from settings or environment
fn get_jwt_secret(settings: &Settings) -> Result<String> {
    settings.security.jwt_secret.clone()
        .or_else(|| std::env::var("AEP_JWT_SECRET").ok())
        .ok_or_else(|| anyhow::anyhow!("JWT secret must be provided via AEP_JWT_SECRET environment variable or config file"))
}

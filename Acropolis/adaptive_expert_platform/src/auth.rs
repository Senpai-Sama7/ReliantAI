//! Authentication and authorization system with JWT support and secure password handling.

use anyhow::{anyhow, Result};
use argon2::{Argon2, PasswordHash, PasswordHasher, PasswordVerifier};
use argon2::password_hash::{rand_core::OsRng, SaltString};
use axum::{
    extract::{Request, State},
    http::{HeaderMap, StatusCode},
    middleware::Next,
    response::Response,
};
use jsonwebtoken::{decode, encode, Algorithm, DecodingKey, EncodingKey, Header, Validation};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tracing::{error, info, warn};

/// JWT claims structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Claims {
    pub sub: String,  // Subject (user ID)
    pub exp: usize,   // Expiration time
    pub iat: usize,   // Issued at
    pub roles: Vec<String>, // User roles
}

/// User authentication information
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct User {
    pub id: String,
    pub username: String,
    pub password_hash: String,
    pub roles: Vec<String>,
    pub active: bool,
}

/// Authentication manager using a persistent sled database
#[derive(Clone)]
pub struct AuthManager {
    db: Arc<sled::Db>,
    jwt_secret: String,
    jwt_expiry_hours: usize,
}

impl AuthManager {
    /// Creates a new AuthManager, opening or creating a sled database at the given path.
    pub fn new(jwt_secret: String, db_path: &str) -> Result<Self> {
        let db = sled::open(db_path)
            .map_err(|e| anyhow!("Failed to open auth database at '{}': {}", db_path, e))?;
        info!("Authentication database opened at '{}'", db_path);
        Ok(Self {
            db: Arc::new(db),
            jwt_secret,
            jwt_expiry_hours: 24, // 24 hour expiry
        })
    }

    /// Initialize the first admin user during setup
    pub fn initialize_admin(&self, username: String, password: &str) -> Result<()> {
        if self.has_admin()? {
            return Err(anyhow!("Admin user already exists. Cannot reinitialize."));
        }

        let password_hash = Self::hash_password(password)?;
        let user = User {
            id: username.clone(),
            username: username.clone(),
            password_hash,
            roles: vec!["admin".to_string(), "user".to_string()],
            active: true,
        };

        let user_bytes = bincode::serialize(&user)?;
        self.db.insert(username.as_bytes(), user_bytes)?;
        self.db.flush()?; // Ensure data is written to disk

        Ok(())
    }

    /// Check if an admin user exists in the database
    pub fn has_admin(&self) -> Result<bool> {
        for item in self.db.iter() {
            let (_, user_bytes) = item?;
            let user: User = bincode::deserialize(&user_bytes)?;
            if user.roles.contains(&"admin".to_string()) {
                return Ok(true);
            }
        }
        Ok(false)
    }

    /// Hash a password securely using Argon2
    pub fn hash_password(password: &str) -> Result<String> {
        let salt = SaltString::generate(&mut OsRng);
        let argon2 = Argon2::default();

        let password_hash = argon2.hash_password(password.as_bytes(), &salt)
            .map_err(|e| anyhow!("Password hashing failed: {}", e))?;

        Ok(password_hash.to_string())
    }

    /// Verify a password against its hash
    pub fn verify_password(password: &str, hash: &str) -> Result<bool> {
        let parsed_hash = PasswordHash::new(hash)
            .map_err(|e| anyhow!("Invalid password hash: {}", e))?;

        let argon2 = Argon2::default();
        Ok(argon2.verify_password(password.as_bytes(), &parsed_hash).is_ok())
    }

    /// Authenticate user and return JWT token
    pub fn authenticate(&self, username: &str, password: &str) -> Result<String> {
        let user_bytes = self.db.get(username.as_bytes())?
            .ok_or_else(|| anyhow!("User not found"))?;

        let user: User = bincode::deserialize(&user_bytes)?;

        if !user.active {
            return Err(anyhow!("User account is disabled"));
        }

        if !Self::verify_password(password, &user.password_hash)? {
            warn!("Failed authentication attempt for user: {}", username);
            return Err(anyhow!("Invalid credentials"));
        }

        info!("Successful authentication for user: {}", username);
        self.generate_token(&user)
    }

    /// Generate JWT token for user
    fn generate_token(&self, user: &User) -> Result<String> {
        let now = chrono::Utc::now();
        let exp = now + chrono::Duration::hours(self.jwt_expiry_hours as i64);

        let claims = Claims {
            sub: user.id.clone(),
            exp: exp.timestamp() as usize,
            iat: now.timestamp() as usize,
            roles: user.roles.clone(),
        };

        let header = Header::new(Algorithm::HS256);
        let encoding_key = EncodingKey::from_secret(self.jwt_secret.as_ref());

        encode(&header, &claims, &encoding_key)
            .map_err(|e| anyhow!("Token generation failed: {}", e))
    }

    /// Validate JWT token and extract claims
    pub fn validate_token(&self, token: &str) -> Result<Claims> {
        let decoding_key = DecodingKey::from_secret(self.jwt_secret.as_ref());
        let validation = Validation::new(Algorithm::HS256);

        let token_data = decode::<Claims>(token, &decoding_key, &validation)
            .map_err(|e| anyhow!("Token validation failed: {}", e))?;

        Ok(token_data.claims)
    }

    /// Check if user has required role
    pub fn has_role(&self, claims: &Claims, required_role: &str) -> bool {
        claims.roles.contains(&required_role.to_string())
    }

    /// Add new user (admin only)
    pub fn add_user(&self, username: String, password: &str, roles: Vec<String>) -> Result<()> {
        if self.db.contains_key(username.as_bytes())? {
            return Err(anyhow!("User already exists"));
        }

        let password_hash = Self::hash_password(password)?;
        let user = User {
            id: username.clone(),
            username: username.clone(),
            password_hash,
            roles,
            active: true,
        };

        let user_bytes = bincode::serialize(&user)?;
        self.db.insert(username.as_bytes(), user_bytes)?;
        self.db.flush()?;
        Ok(())
    }

    /// Update user password
    pub fn update_password(&self, username: &str, new_password: &str) -> Result<()> {
        let mut user = self.get_user(username)?;
        user.password_hash = Self::hash_password(new_password)?;
        self.update_user(&user)
    }

    /// Disable user account
    pub fn disable_user(&self, username: &str) -> Result<()> {
        let mut user = self.get_user(username)?;
        user.active = false;
        self.update_user(&user)
    }

    fn get_user(&self, username: &str) -> Result<User> {
        let user_bytes = self.db.get(username)?.ok_or_else(|| anyhow!("User not found"))?;
        let user: User = bincode::deserialize(&user_bytes)?;
        Ok(user)
    }

    fn update_user(&self, user: &User) -> Result<()> {
        let user_bytes = bincode::serialize(user)?;
        self.db.insert(user.username.as_bytes(), user_bytes)?;
        self.db.flush()?;
        Ok(())
    }
}

/// Extract JWT token from Authorization header
pub fn extract_token(headers: &HeaderMap) -> Result<String> {
    let auth_header = headers.get("Authorization")
        .ok_or_else(|| anyhow!("Missing Authorization header"))?
        .to_str()
        .map_err(|_| anyhow!("Invalid Authorization header"))?;

    if !auth_header.starts_with("Bearer ") {
        return Err(anyhow!("Invalid Authorization format"));
    }

    Ok(auth_header[7..].to_string())
}

/// Authentication middleware
pub async fn auth_middleware(
    State(auth_manager): State<Arc<AuthManager>>,
    mut request: Request,
    next: Next,
) -> Result<Response, StatusCode> {
    // Skip authentication for health endpoint
    if request.uri().path() == "/health" {
        return Ok(next.run(request).await);
    }

    let token = match extract_token(request.headers()) {
        Ok(token) => token,
        Err(_) => {
            warn!("Unauthorized request to {}", request.uri().path());
            return Err(StatusCode::UNAUTHORIZED);
        }
    };

    match auth_manager.validate_token(&token) {
        Ok(claims) => {
            // Add claims to request extensions for downstream use
            request.extensions_mut().insert(claims);
            Ok(next.run(request).await)
        }
        Err(e) => {
            error!("Token validation failed: {}", e);
            Err(StatusCode::UNAUTHORIZED)
        }
    }
}

/// Role-based authorization middleware
pub fn require_role(required_role: &'static str) -> impl Fn(Request, Next) -> std::pin::Pin<Box<dyn std::future::Future<Output = Result<Response, StatusCode>> + Send>> + Clone {
    move |request: Request, next: Next| {
        Box::pin(async move {
            let claims = request.extensions().get::<Claims>()
                .ok_or(StatusCode::INTERNAL_SERVER_ERROR)?;

            if !claims.roles.contains(&required_role.to_string()) {
                warn!("Insufficient permissions for user {} to access {}", claims.sub, request.uri().path());
                return Err(StatusCode::FORBIDDEN);
            }

            Ok(next.run(request).await)
        })
    }
}

/// Login request structure
#[derive(Deserialize)]
pub struct LoginRequest {
    pub username: String,
    pub password: String,
}

/// Login response structure
#[derive(Serialize)]
pub struct LoginResponse {
    pub token: String,
    pub expires_in: usize,
    pub user_id: String,
    pub roles: Vec<String>,
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    fn create_test_auth_manager() -> AuthManager {
        let dir = tempdir().unwrap();
        AuthManager::new("test_secret".to_string(), dir.path().to_str().unwrap()).unwrap()
    }

    #[test]
    fn test_password_hashing() {
        let password = "test_password_123!";
        let hash = AuthManager::hash_password(password).unwrap();
        assert!(AuthManager::verify_password(password, &hash).unwrap());
        assert!(!AuthManager::verify_password("wrong_password", &hash).unwrap());
    }

    #[test]
    fn test_user_management() {
        let auth_manager = create_test_auth_manager();
        let username = "test_user".to_string();
        let password = "test_password_123!";
        let roles = vec!["user".to_string()];

        // Add user
        auth_manager.add_user(username.clone(), password, roles.clone()).unwrap();

        // Authenticate user
        let token = auth_manager.authenticate(&username, password).unwrap();
        let claims = auth_manager.validate_token(&token).unwrap();
        assert_eq!(claims.sub, username);
        assert_eq!(claims.roles, roles);

        // Disable user
        auth_manager.disable_user(&username).unwrap();
        let err = auth_manager.authenticate(&username, password).unwrap_err();
        assert_eq!(err.to_string(), "User account is disabled");
    }

    #[test]
    fn test_admin_initialization() {
        let auth_manager = create_test_auth_manager();
        assert!(!auth_manager.has_admin().unwrap());

        auth_manager.initialize_admin("admin".to_string(), "admin_password").unwrap();
        assert!(auth_manager.has_admin().unwrap());

        // Should fail to initialize again
        assert!(auth_manager.initialize_admin("admin2".to_string(), "admin_password2").is_err());
    }
}

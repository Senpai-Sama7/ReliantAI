//! Security middleware for rate limiting, request size validation, and CORS handling.

use axum::{
    extract::{Request, State},
    http::{HeaderValue, Method, StatusCode},
    middleware::Next,
    response::Response,
};
use governor::{
    clock::DefaultClock,
    state::{InMemoryState, NotKeyed},
    Quota, RateLimiter,
};
use std::{num::NonZeroU32, sync::Arc};
use tower_http::{
    cors::{Any, CorsLayer},
    limit::RequestBodyLimitLayer,
};
use tracing::warn;

use crate::settings::SecurityConfig;

/// Rate limiter type
pub type AppRateLimiter = RateLimiter<NotKeyed, InMemoryState, DefaultClock>;

/// Create rate limiter from configuration
pub fn create_rate_limiter(config: &SecurityConfig) -> Arc<AppRateLimiter> {
    let quota = Quota::per_minute(NonZeroU32::new(config.rate_limit_per_minute).unwrap());
    Arc::new(RateLimiter::direct(quota))
}

/// Rate limiting middleware
pub async fn rate_limit_middleware(
    State(rate_limiter): State<Arc<AppRateLimiter>>,
    request: Request,
    next: Next,
) -> Result<Response, StatusCode> {
    match rate_limiter.check() {
        Ok(_) => Ok(next.run(request).await),
        Err(_) => {
            warn!("Rate limit exceeded for request to {}", request.uri().path());
            Err(StatusCode::TOO_MANY_REQUESTS)
        }
    }
}

/// Request size validation middleware
pub async fn request_size_middleware(
    request: Request,
    next: Next,
) -> Result<Response, StatusCode> {
    // Size limiting is handled by RequestBodyLimitLayer
    // This middleware can add additional validation if needed
    Ok(next.run(request).await)
}

/// Security headers middleware
pub async fn security_headers_middleware(
    request: Request,
    next: Next,
) -> Result<Response, StatusCode> {
    let mut response = next.run(request).await;

    let headers = response.headers_mut();

    // Add security headers
    headers.insert("X-Content-Type-Options", HeaderValue::from_static("nosniff"));
    headers.insert("X-Frame-Options", HeaderValue::from_static("DENY"));
    headers.insert("X-XSS-Protection", HeaderValue::from_static("1; mode=block"));
    headers.insert("Strict-Transport-Security", HeaderValue::from_static("max-age=31536000; includeSubDomains"));
    headers.insert("Referrer-Policy", HeaderValue::from_static("strict-origin-when-cross-origin"));
    headers.insert("Permissions-Policy", HeaderValue::from_static("camera=(), microphone=(), geolocation=()"));

    Ok(response)
}

/// Create CORS layer from security configuration
pub fn create_cors_layer(config: &SecurityConfig) -> CorsLayer {
    if config.enable_cors {
        let mut cors = CorsLayer::new()
            .allow_methods([Method::GET, Method::POST, Method::PUT, Method::DELETE])
            .allow_headers([
                axum::http::header::AUTHORIZATION,
                axum::http::header::CONTENT_TYPE,
                axum::http::header::ACCEPT,
            ]);

        // Configure allowed origins
        if config.allowed_origins.contains(&"*".to_string()) {
            cors = cors.allow_origin(Any);
        } else {
            for origin in &config.allowed_origins {
                if let Ok(header_value) = HeaderValue::from_str(origin) {
                    cors = cors.allow_origin(header_value);
                }
            }
        }

        cors
    } else {
        // Restrictive CORS when disabled
        CorsLayer::new()
            .allow_origin("http://localhost".parse::<HeaderValue>().unwrap())
            .allow_methods([Method::GET])
    }
}

/// Create request body size limit layer
pub fn create_body_limit_layer(max_size_mb: usize) -> RequestBodyLimitLayer {
    RequestBodyLimitLayer::new(max_size_mb * 1024 * 1024)
}

/// IP-based rate limiting (for future enhancement)
pub struct IpRateLimiter {
    // Implementation would go here for per-IP rate limiting
    // This is a placeholder for more sophisticated rate limiting
}

impl IpRateLimiter {
    pub fn new() -> Self {
        Self {}
    }

    pub async fn check_ip(&self, _ip: &str) -> bool {
        // Placeholder implementation
        true
    }
}

/// Logging middleware for security events
pub async fn security_logging_middleware(
    request: Request,
    next: Next,
) -> Result<Response, StatusCode> {
    let method = request.method().clone();
    let uri = request.uri().clone();
    let headers = request.headers().clone();

    // Log potentially suspicious requests
    if let Some(user_agent) = headers.get("User-Agent") {
        if let Ok(ua_str) = user_agent.to_str() {
            if ua_str.contains("bot") || ua_str.contains("crawler") || ua_str.contains("spider") {
                warn!("Bot/crawler detected: {} {} - UA: {}", method, uri, ua_str);
            }
        }
    }

    // Check for suspicious headers
    if headers.get("X-Forwarded-For").is_some() && headers.get("X-Real-IP").is_some() {
        warn!("Multiple proxy headers detected for request: {} {}", method, uri);
    }

    let response = next.run(request).await;

    // Log error responses
    if response.status().is_client_error() || response.status().is_server_error() {
        warn!("Error response: {} {} - Status: {}", method, uri, response.status());
    }

    Ok(response)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_rate_limiter() {
        let config = SecurityConfig {
            rate_limit_per_minute: 2,
            ..Default::default()
        };

        let rate_limiter = create_rate_limiter(&config);

        // First two requests should succeed
        assert!(rate_limiter.check().is_ok());
        assert!(rate_limiter.check().is_ok());

        // Third request should be rate limited
        assert!(rate_limiter.check().is_err());
    }

    #[test]
    fn test_cors_configuration() {
        let config = SecurityConfig {
            enable_cors: true,
            allowed_origins: vec!["https://example.com".to_string()],
            ..Default::default()
        };

        let _cors_layer = create_cors_layer(&config);
        // Testing CORS layer configuration would require more complex setup
        // This is a basic structure test
    }
}

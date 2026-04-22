//! FFI bindings and helpers for calling Zig functions from Rust.
//!
//! When the `zig` feature is enabled this module exposes a sample
//! [`Agent`](crate::agent::Agent) that demonstrates how to call into a
//! function defined in a Zig dynamic library.  Zig has excellent C
//! interop, so the recommended way to build Zig code for Rust is to
//! compile it as a C-compatible dynamic library and declare the
//! exported functions using the `extern` keyword in Rust.  See the
//! following example from the Zig manual for details:
//!
//! ```zig
//! const std = @import("std");
//!
//! // Export an addition function so it can be called from C/Rust
//! export fn zig_add(a: i32, b: i32) i32 {
//!     return a + b;
//! }
//! ```
//!
//! The companion Rust declaration looks like this:
//!
//! ```rust
//! extern "C" {
//!     fn zig_add(a: i32, b: i32) -> i32;
//! }
//! ```
//!
//! You must build the Zig library as a shared object (e.g. using
//! `zig build-lib mylib.zig -dynamic`) and ensure that it is on your
//! library search path at runtime.  The Rust compiler will link
//! against it if the appropriate linker flags are provided.  See the
//! [DEV Community article on using Zig in Rust] for an example of
//! building and linking a Zig library from Rust【486881172987055†L52-L86】.
//!
//! This module defines a [`ZigAgent`] which parses its input as two
//! integers separated by a comma and returns their sum using the Zig
//! function.  If parsing fails an error is returned.

use crate::agent::Agent;
use crate::memory::Memory;
use anyhow::{anyhow, Result};
use async_trait::async_trait;
use serde::Deserialize;
use std::sync::Arc;
use tracing::{instrument, warn};

/// Maximum safe integer value for FFI operations to prevent overflow
const MAX_SAFE_INTEGER: i32 = 1_000_000;
/// Minimum safe integer value for FFI operations
const MIN_SAFE_INTEGER: i32 = -1_000_000;

/// Input validation structure for Zig operations
#[derive(Deserialize)]
struct ZigAddInput {
    a: i32,
    b: i32,
}

/// Foreign function imported from the Zig library.  This signature
/// must match the exported function in Zig exactly.  The function
/// performs integer addition and returns the result.
#[cfg(feature = "zig")]
extern "C" {
    fn zig_add(a: i32, b: i32) -> i32;
}

/// Validates integer inputs for safe FFI operations
fn validate_ffi_input(a: i32, b: i32) -> Result<()> {
    if a < MIN_SAFE_INTEGER || a > MAX_SAFE_INTEGER {
        return Err(anyhow!("Integer 'a' ({}) outside safe range [{}, {}]", a, MIN_SAFE_INTEGER, MAX_SAFE_INTEGER));
    }
    if b < MIN_SAFE_INTEGER || b > MAX_SAFE_INTEGER {
        return Err(anyhow!("Integer 'b' ({}) outside safe range [{}, {}]", b, MIN_SAFE_INTEGER, MAX_SAFE_INTEGER));
    }

    // Check for potential overflow in addition
    if (a > 0 && b > i32::MAX - a) || (a < 0 && b < i32::MIN - a) {
        return Err(anyhow!("Addition of {} and {} would cause integer overflow", a, b));
    }

    Ok(())
}

/// An agent that delegates addition to a Zig function via FFI.
///
/// The `ZigAgent` expects an input JSON in the form {"a": 123, "b": 456} where
/// `a` and `b` are 32-bit integers within safe bounds.  It validates input,
/// performs bounds checking, and then calls the `zig_add` function.  The result
/// is returned to the caller.  All parsing and FFI calls include comprehensive
/// error handling and safety checks.
#[cfg(feature = "zig")]
pub struct ZigAgent;

#[cfg(feature = "zig")]
impl ZigAgent {
    /// Create a new instance of the agent.  No state is stored.
    pub fn new() -> Self {
        Self
    }
}

#[cfg(feature = "zig")]
#[async_trait]
impl Agent for ZigAgent {
    fn name(&self) -> &str {
        "zig"
    }

    fn agent_type(&self) -> &str {
        "native_utility"
    }

    fn capabilities(&self) -> Vec<String> {
        vec!["addition".to_string()]
    }

    async fn health_check(&self) -> Result<crate::agent::AgentHealth> {
        // Zig FFI is synchronous and stateless, so it's always healthy if the library is loaded.
        Ok(crate::agent::AgentHealth::default())
    }

    #[instrument(skip(self, memory), fields(agent = "zig"))]
    async fn handle(&self, input: serde_json::Value, _memory: Arc<Memory>) -> Result<String> {
        // Parse and validate input JSON structure
        let parsed_input: ZigAddInput = serde_json::from_value(input)
            .map_err(|e| anyhow!("Invalid JSON input for ZigAgent: {}. Expected {{\"a\": number, \"b\": number}}", e))?;

        let a = parsed_input.a;
        let b = parsed_input.b;

        // Comprehensive input validation
        validate_ffi_input(a, b)?;

        // SAFETY: We have validated that:
        // 1. Both inputs are within safe integer bounds
        // 2. The addition will not overflow
        // 3. The Zig function signature matches our declaration
        // 4. We trust the Zig library to adhere to the C ABI
        let result = unsafe {
            tracing::debug!("Calling zig_add({}, {})", a, b);
            zig_add(a, b)
        };

        // Validate result is within expected bounds
        let expected = a.saturating_add(b);
        if result != expected {
            warn!("Zig FFI result mismatch: expected {}, got {}", expected, result);
            return Err(anyhow!("FFI result validation failed: expected {}, got {}", expected, result));
        }

        Ok(result.to_string())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validate_ffi_input_valid() {
        assert!(validate_ffi_input(100, 200).is_ok());
        assert!(validate_ffi_input(-100, 200).is_ok());
        assert!(validate_ffi_input(0, 0).is_ok());
    }

    #[test]
    fn test_validate_ffi_input_overflow() {
        assert!(validate_ffi_input(i32::MAX, 1).is_err());
        assert!(validate_ffi_input(i32::MIN, -1).is_err());
    }

    #[test]
    fn test_validate_ffi_input_out_of_bounds() {
        assert!(validate_ffi_input(MAX_SAFE_INTEGER + 1, 0).is_err());
        assert!(validate_ffi_input(MIN_SAFE_INTEGER - 1, 0).is_err());
    }
}

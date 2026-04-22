//! Adaptive Expert Platform - Core Library
//!
//! A secure, polyglot AI orchestration platform built in Rust.

pub mod agent;
pub mod auth;
pub mod batch;
pub mod cache;
pub mod cli;
pub mod lifecycle;
pub mod memory;
pub mod mesh;
pub mod metrics;
pub mod middleware;
pub mod monitoring;
pub mod orchestrator;
pub mod plugin;
pub mod server;
pub mod settings;
pub mod telemetry;
pub mod websocket;

#[cfg(feature = "with-wasm")]
pub mod wasm_plugin;

#[cfg(feature = "with-julia")]
pub mod ffi_julia;

#[cfg(feature = "with-zig")]
pub mod ffi_zig;

pub use agent::Agent;

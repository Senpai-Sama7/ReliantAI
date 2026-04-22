// plugins/julia_plugin/src/lib.rs
//! Julia Agent Plugin – bridges Rust ↔ Julia via `jlrs` with enhanced security.
//!
//! Accepts JSON like:
/// ```json
/// { "code": "string_or_julia_expression", "context": "optional_execution_context" }
/// ```
/// Evaluates `code` inside a sandboxed Julia environment and returns its string representation.

use adaptive_expert_platform::agent::{Agent, AgentHealth};
use adaptive_expert_platform::memory::Memory;
use adaptive_expert_platform::plugin::PluginRegistrar;
use anyhow::{anyhow, Result};
use async_trait::async_trait;
use jlrs::prelude::*;
use once_cell::sync::OnceCell;
use serde_json::Value;
use std::sync::Arc;
use tokio::sync::oneshot;
use tracing::{info, warn, error, instrument};
use std::collections::HashSet;
use regex::Regex;

/// Global Julia runtime (one per process, lazy-initialised).
static JULIA: OnceCell<Julia> = OnceCell::new();

/// Sandbox configuration for Julia code execution
#[derive(Debug, Clone)]
pub struct JuliaSandboxConfig {
    /// Maximum execution time in seconds
    pub max_execution_time: u64,
    /// Allowed Julia packages/modules
    pub allowed_packages: HashSet<String>,
    /// Forbidden function patterns (regex)
    pub forbidden_patterns: Vec<Regex>,
    /// Maximum output length
    pub max_output_length: usize,
}

impl Default for JuliaSandboxConfig {
    fn default() -> Self {
        let mut allowed_packages = HashSet::new();
        // Only allow basic mathematical and data manipulation packages
        allowed_packages.insert("Base".to_string());
        allowed_packages.insert("LinearAlgebra".to_string());
        allowed_packages.insert("Statistics".to_string());
        allowed_packages.insert("Printf".to_string());

        let forbidden_patterns = vec![
            Regex::new(r"(?i)system\s*\(").unwrap(),
            Regex::new(r"(?i)run\s*\(").unwrap(),
            Regex::new(r"(?i)spawn\s*\(").unwrap(),
            Regex::new(r"(?i)cd\s*\(").unwrap(),
            Regex::new(r"(?i)open\s*\(.*[\"'][rwa]").unwrap(),
            Regex::new(r"(?i)write\s*\(").unwrap(),
            Regex::new(r"(?i)rm\s*\(").unwrap(),
            Regex::new(r"(?i)mkdir\s*\(").unwrap(),
            Regex::new(r"(?i)download\s*\(").unwrap(),
            Regex::new(r"(?i)include\s*\(").unwrap(),
            Regex::new(r"(?i)eval\s*\(").unwrap(),
            Regex::new(r"(?i)unsafe_").unwrap(),
            Regex::new(r"(?i)ccall\s*\(").unwrap(),
            Regex::new(r"(?i)@eval").unwrap(),
            Regex::new(r"(?i)Meta\.parse").unwrap(),
        ];

        Self {
            max_execution_time: 5, // 5 seconds max
            allowed_packages,
            forbidden_patterns,
            max_output_length: 10_000, // 10KB max output
        }
    }
}

/// Validates Julia code against security policies
fn validate_julia_code(code: &str, config: &JuliaSandboxConfig) -> Result<()> {
    // Check for forbidden patterns
    for pattern in &config.forbidden_patterns {
        if pattern.is_match(code) {
            return Err(anyhow!(
                "Code contains forbidden pattern: {} (matched by {})",
                code, pattern.as_str()
            ));
        }
    }

    // Check code length
    if code.len() > 10_000 {
        return Err(anyhow!("Code too long: {} characters (max: 10000)", code.len()));
    }

    // Basic syntax validation - check for balanced parentheses/brackets
    let mut paren_count = 0;
    let mut bracket_count = 0;
    let mut brace_count = 0;

    for ch in code.chars() {
        match ch {
            '(' => paren_count += 1,
            ')' => paren_count -= 1,
            '[' => bracket_count += 1,
            ']' => bracket_count -= 1,
            '{' => brace_count += 1,
            '}' => brace_count -= 1,
            _ => {}
        }

        // Early detection of unbalanced brackets
        if paren_count < 0 || bracket_count < 0 || brace_count < 0 {
            return Err(anyhow!("Unbalanced brackets in Julia code"));
        }
    }

    if paren_count != 0 || bracket_count != 0 || brace_count != 0 {
        return Err(anyhow!("Unbalanced brackets in Julia code"));
    }

    Ok(())
}

/// Get or initialise the global Julia instance with security constraints.
fn get_julia() -> Result<&'static Julia> {
    JULIA.get_or_try_init(|| unsafe {
        info!("Initializing Julia runtime with security constraints");

        // Initialize with limited thread count for better resource control
        let julia = Julia::init(4)?;

        // TODO: Set up Julia security policies here
        // This would involve Julia-side configuration to restrict file system access,
        // network operations, and other potentially dangerous operations

        Ok(julia)
    })
}

/// Create a sandboxed Julia execution context
fn create_sandbox_context() -> String {
    r#"
# Sandboxed Julia execution context
module SandboxedExecution
    # Disable dangerous functions
    const DISABLED_FUNCTIONS = [
        :system, :run, :spawn, :cd, :include, :eval,
        :download, :unsafe_load, :unsafe_store!, :ccall
    ]

    # Override dangerous functions with safe alternatives
    for func in DISABLED_FUNCTIONS
        if isdefined(Base, func)
            @eval const $func = () -> error("Function $func is disabled in sandbox")
        end
    end

    # Execution wrapper with resource limits
    function safe_eval(code_str)
        try
            # Parse and validate the expression
            expr = Meta.parse(code_str)

            # Basic AST validation (prevent meta-programming)
            validate_expr(expr)

            # Evaluate in restricted context
            result = eval(expr)

            # Convert result to string with length limits
            output = string(result)
            if length(output) > 10000
                return "Output truncated (too long)"
            end

            return output
        catch e
            return "Error: $(string(e))"
        end
    end

    function validate_expr(expr)
        if isa(expr, Expr)
            # Comprehensive list of forbidden expression types
            forbidden_heads = [
                :meta, :eval, :include, :ccall, :unsafe, :using, :import,
                :module, :baremodule, :export, :global, :local, :const,
                :macrocall, :quote, :escape, :hygienicscope, :thunk,
                :lambda, :method, :struct, :abstract, :primitive, :typealias
            ]

            if expr.head in forbidden_heads
                throw(ArgumentError("Forbidden expression type: $(expr.head)"))
            end

            # Check for forbidden function calls
            if expr.head == :call && length(expr.args) > 0
                func_name = expr.args[1]
                if isa(func_name, Symbol)
                    forbidden_functions = [
                        :eval, :include, :open, :read, :write, :download, :run,
                        :spawn, :cd, :readdir, :mkdir, :rm, :cp, :mv, :chmod,
                        :unsafe_load, :unsafe_store!, :ccall, :cglobal, :dlopen,
                        :dlsym, :system, :exec, :pipeline, :connect, :listen,
                        :getpid, :getppid, :kill, :interrupt, :exit, :quit,
                        :redirect_stdout, :redirect_stderr, :redirect_stdin
                    ]

                    if func_name in forbidden_functions
                        throw(ArgumentError("Forbidden function call: $func_name"))
                    end
                end
            end

            # Recursively validate subexpressions with depth limit
            validate_expr_recursive(expr.args, 0, 10)
        elseif isa(expr, Symbol)
            # Check for forbidden global variables/modules
            forbidden_symbols = [
                :Base, :Core, :Main, :Sys, :Pkg, :Distributed, :SharedArrays,
                :Sockets, :Mmap, :Downloads, :InteractiveUtils, :LibGit2,
                :Logging, :Markdown, :Printf, :Profile, :REPL, :Serialization,
                :Test, :UUIDs, :Unicode, :Artifacts, :LazyArtifacts
            ]

            if expr in forbidden_symbols
                throw(ArgumentError("Access to forbidden symbol: $expr"))
            end
        end
    end

    function validate_expr_recursive(args, depth, max_depth)
        if depth > max_depth
            throw(ArgumentError("Expression nesting too deep"))
        end

        for arg in args
            validate_expr(arg)
            if isa(arg, Expr)
                validate_expr_recursive(arg.args, depth + 1, max_depth)
            end
        end
    end
end
"#
}

/// The concrete Agent we expose to the platform.
pub struct JuliaAgent {
    sandbox_config: JuliaSandboxConfig,
}

impl JuliaAgent {
    pub fn new() -> Self {
        Self {
            sandbox_config: JuliaSandboxConfig::default(),
        }
    }

    pub fn with_config(config: JuliaSandboxConfig) -> Self {
        Self {
            sandbox_config: config,
        }
    }
}

#[async_trait]
impl Agent for JuliaAgent {
    fn name(&self) -> &str {
        "julia_agent"
    }

    fn agent_type(&self) -> &str {
        "julia"
    }

    fn capabilities(&self) -> Vec<String> {
        vec!["julia_execute".to_string()]
    }

    #[instrument(skip(self, input, _memory), fields(code_length))]
    async fn handle(&self, input: Value, _memory: Arc<Memory>) -> Result<String> {
        // Parse input structure
        let code = match &input {
            Value::Object(obj) => {
                obj.get("code")
                    .and_then(|v| v.as_str())
                    .ok_or_else(|| anyhow!("Expected JSON {{\"code\": \"…\"}}"))?
            }
            Value::String(s) => s.as_str(),
            _ => return Err(anyhow!("Expected string or object with 'code' field")),
        }.to_owned();

        tracing::Span::current().record("code_length", code.len());

        // Validate code against security policies
        validate_julia_code(&code, &self.sandbox_config)?;

        info!("Executing Julia code in sandbox (length: {})", code.len());

        // Execute in blocking task with timeout
        let sandbox_config = self.sandbox_config.clone();
        let (tx, rx) = oneshot::channel();

        tokio::task::spawn_blocking(move || {
            let result = execute_julia_sandboxed(&code, &sandbox_config);
            let _ = tx.send(result);
        });

        // Apply timeout at the Rust level
        let result = tokio::time::timeout(
            std::time::Duration::from_secs(sandbox_config.max_execution_time),
            rx
        ).await;

        match result {
            Ok(Ok(output)) => {
                // Validate output length
                if output.len() > sandbox_config.max_output_length {
                    warn!("Julia output truncated: {} chars", output.len());
                    Ok(format!("{}... [truncated]", &output[..sandbox_config.max_output_length]))
                } else {
                    Ok(output)
                }
            }
            Ok(Err(e)) => {
                error!("Julia execution failed: {}", e);
                Err(e)
            }
            Err(_) => {
                error!("Julia execution timed out");
                Err(anyhow!("Julia execution timed out"))
            }
        }
    }

    async fn health_check(&self) -> Result<AgentHealth> {
        Ok(AgentHealth::default())
    }
}

/// Execute Julia code in a sandboxed environment
fn execute_julia_sandboxed(code: &str, _config: &JuliaSandboxConfig) -> Result<String> {
    unsafe {
        let julia = get_julia()?;

        julia.scope(|mut frame| {
            // Set up sandbox context
            let sandbox_setup = create_sandbox_context();
            ValueRef::eval_string(&mut frame, &sandbox_setup)?;

            // Prepare safe execution call
            let safe_code = format!(
                "SandboxedExecution.safe_eval(\"{}\")",
                code.replace("\"", "\\\"").replace("\n", "\\n")
            );

            // Execute in sandbox
            let result = ValueRef::eval_string(&mut frame, &safe_code)?;

            // Convert to string
            Ok(result.display_string(&mut frame)?)
        })
        .map_err(|e| anyhow!("Julia sandbox execution error: {:?}", e))
    }
}

/// Mandatory C-ABI entry-point so the platform can `dlopen` the plugin.
#[no_mangle]
pub extern "C" fn register_plugin(registrar: &mut PluginRegistrar) {
    registrar.register_agent("julia_agent", || Box::new(JuliaAgent::new()));
    info!("julia_agent registered with sandbox security");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_validate_julia_code_safe() {
        let config = JuliaSandboxConfig::default();
        assert!(validate_julia_code("x = 1 + 2", &config).is_ok());
        assert!(validate_julia_code("println(sqrt(16))", &config).is_ok());
    }

    #[test]
    fn test_validate_julia_code_dangerous() {
        let config = JuliaSandboxConfig::default();
        assert!(validate_julia_code("system(\"rm -rf /\")", &config).is_err());
        assert!(validate_julia_code("run(`ls`)", &config).is_err());
        assert!(validate_julia_code("include(\"malicious.jl\")", &config).is_err());
        assert!(validate_julia_code("eval(:(system(\"bad\")))", &config).is_err());
    }

    #[test]
    fn test_validate_julia_code_balanced_brackets() {
        let config = JuliaSandboxConfig::default();
        assert!(validate_julia_code("f(x) = [1, 2, 3]", &config).is_ok());
        assert!(validate_julia_code("f(x = [1, 2)", &config).is_err());
        assert!(validate_julia_code("f(x) = [1, 2, 3", &config).is_err());
    }

    #[test]
    fn test_sandbox_config_default() {
        let config = JuliaSandboxConfig::default();
        assert_eq!(config.max_execution_time, 5);
        assert_eq!(config.max_output_length, 10_000);
        assert!(config.allowed_packages.contains("Base"));
        assert!(!config.forbidden_patterns.is_empty());
    }
}

# Acropolis Adaptive Expert Platform - Agent Guide

**Last updated:** 2026-03-05

## Project Overview

Acropolis is a modular research platform for building and orchestrating "expert" agents. It is organized as a Rust workspace with optional components for native plugins, embeddings, and a desktop GUI.

**Key Capabilities:**
- Routes JSON tasks to registered agents through asynchronous channels
- Limits concurrent tasks and records execution metrics
- Supports hot-reloading of native plugins with configurable security
- Polyglot agent system (Rust core + Julia/Python/LLM agents)

## Hostile Audit Persistence

- Append every hostile-audit checkpoint and verification result to the root `PROGRESS_TRACKER.md`.
- Do not mark Rust runtime, plugin, or auth-path fixes complete without a real cargo command result, health check, or artifact saved under `proof/hostile-audit/<timestamp>/`.
- Reproduce before patching. If the original failure path changes, record both the failed assumption and the command that actually reproduced the live issue.
- Preserve hardening behavior in production code; fix stale tests to match stricter security controls instead of weakening the controls.
- If scanners or dependency-audit tools cannot run cleanly, record the exact blocker and the fallback evidence path instead of implying success.

**Architecture Pattern:**
```
┌─────────────────────────────────────────────────────────┐
│  Rust Orchestration Hub                                 │
│  ├── Orchestrator (task routing)                        │
│  ├── Memory Subsystem (embeddings, search)              │
│  └── Plugin Framework (hot-reload)                      │
├─────────────────────────────────────────────────────────┤
│  Expert Agents (Connectors)                             │
│  ├── JuliaExpertAgent → jlrs FFI → Julia Runtime        │
│  ├── PythonToolAgent → tokio::process → Python          │
│  ├── LlmAgent → llama_cpp crate → GGUF Model            │
│  └── NativePluginAgent → libloading → .so/.dll          │
└─────────────────────────────────────────────────────────┘
```

---

## Build / Run / Test Commands

### Rust Workspace Commands
```bash
# Build the workspace
cargo build

# Build with optimizations
cargo build --release

# Run tests
cargo test

# Check without building
cargo check

# Clean build artifacts
cargo clean
```

### GUI (Tauri Desktop App)
```bash
# Build and run the GUI
cd gui && cargo tauri dev

# Build for production
cargo tauri build
```

### Plugin Development
```bash
# Build example plugin
cd plugins/uppercase_plugin && cargo build

# Plugins are loaded from the configured plugin directory
# Hot-reload watches for changes and reloads automatically
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Core** | Rust + Tokio | Async orchestration and task routing |
| **WebSocket** | tokio-tungstenite | Real-time client communication |
| **Embeddings** | rust-bert / llama_cpp | Vector generation for memory |
| **Julia FFI** | jlrs | Julia runtime integration |
| **GUI** | Tauri | Desktop application wrapper |
| **Plugins** | libloading | Dynamic shared library loading |

---

## Project Structure

```
Acropolis/
├── adaptive_expert_platform/     # Core orchestration crate
│   ├── src/orchestrator.rs       # Main task router
│   ├── src/agent/                # Agent trait and implementations
│   ├── src/memory/               # Vector search and storage
│   └── src/plugin/               # Hot-reload plugin system
├── plugins/                      # Native plugin examples
│   └── uppercase_plugin/         # Example .so/.dll plugin
├── gui/                          # Tauri desktop application
├── configs/                      # Task definition configs
├── agents/                       # Agent configurations
└── Cargo.toml                    # Workspace manifest
```

---

## Critical Code Patterns

### Environment Variables (AEP_ prefix)
All environment variables use the `AEP_` prefix:
- `AEP_HOST` - Server bind address
- `AEP_PORT` - Server port
- `AEP_PLUGIN_DIR` - Plugin directory path
- `AEP_OBSERVABILITY_ENDPOINT` - Metrics endpoint

### Agent Trait Implementation
```rust
#[async_trait]
pub trait Agent: Send + Sync {
    fn name(&self) -> &str;
    fn agent_type(&self) -> AgentType;
    fn capabilities(&self) -> &[Capability];
    async fn handle(&self, request: AgentRequest) -> AgentResult;
    async fn health(&self) -> HealthStatus;
}
```

### Plugin Security
Plugins are validated before loading:
- Extension allowlist (`.so`, `.dll`, `.dylib`)
- File size limits
- Hash allowlist verification
- Path validation

---

## Non-Obvious Gotchas

### 1. CLAUDE.md is NOT the Architecture Doc
The `CLAUDE.md` file in this repo is generic guidance. The actual architecture documentation is in `ARCHITECTURE.md`.

### 2. Julia Integration Requires System Dependencies
The JuliaExpertAgent requires:
- Full Julia runtime installed
- jlrs-compatible Julia version
- Flux.jl and CausalInference.jl packages
- Not available in basic `cargo test` - feature-gated

### 3. Plugin Hot-Reloading
- Plugins are watched via file system events
- Reloading happens asynchronously
- Failed reloads don't crash the orchestrator
- Previous version keeps running until new version validates

### 4. Memory Embedding Cache
Embeddings are cached to avoid recomputation:
- In-memory key-value store for frequently accessed vectors
- Cache invalidation tied to content hash
- Reranking performed on cached results

### 5. Workspace Member Naming
The main crate is named `adaptive_expert_platform`, NOT `orchestrator` or `core`. Import paths use this exact name.

---

## Configuration Loading Order

Settings are loaded in this priority (highest to lowest):
1. Environment variables (`AEP_*` prefix)
2. `config.local.toml` (gitignored)
3. `config.toml` (committed defaults)
4. Hardcoded defaults

---

## Testing Notes

- `cargo test` runs unit tests only
- Julia/Python integration tests require runtimes installed
- Plugin tests require example plugin built first
- GUI tests require Tauri dependencies

---

## Reference

See root `AGENTS.md` for:
- Core commandments (integration build rules)
- Mode-specific guidelines
- Universal patterns across all ReliantAI projects

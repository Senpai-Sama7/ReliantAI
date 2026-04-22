# Acropolis Adaptive Expert Platform

Acropolis is a modular research platform for building and orchestrating "expert" agents.
It is organized as a Rust workspace with optional components for native plugins,
embeddings, and a desktop GUI.

## Orchestrator
* Routes JSON tasks to registered agents through an asynchronous channel.
* Limits concurrent tasks and records execution metrics.
* Initializes subsystems for lifecycle management, monitoring, multi-tier cache,
  a websocket server, and optional mesh networking.
* Supports hot-reloading of native plugins with configurable security.

## Agent System
* `Agent` trait defines name, type, capabilities, request handling, and health checks.
* Built-in agents:
  * **EchoAgent** – returns the provided input for testing.
  * **HashEmbeddingAgent** – generates deterministic embeddings for text.
  * **PythonToolAgent** – executes whitelisted Python scripts with path, argument,
    and hash validation.
  * **LlmAgent** – uses `llama_cpp` for text generation when the `with-llama` feature is enabled.
* `AgentFactory` can create agents by type (echo, python, optional Julia/Zig/LLM).

## Memory Subsystem
* Stores `MemoryFragment` structures containing content, embeddings, metadata, and tags.
* Generates embeddings via an embedding agent and caches them to avoid recomputation.
* Provides vector similarity search with reranking and an in-memory key-value store.

## Plugin Framework
* Loads native agents from shared libraries (`.so`, `.dll`, `.dylib`).
* Enforces extension allowlists, file-size limits, and hash allowlists before loading.
* Watches the plugin directory for changes to reload updated agents.
* Example plugin `uppercase_plugin` converts text to uppercase.

## Configuration
* `Settings` load defaults from `config.toml`, optional local files, and environment variables.
* Environment variables with the `AEP_` prefix override critical fields such as server host,
  port, plugin directory, observability endpoints, and security secrets.
* Validation ensures sane values (e.g., non-zero server port, plugin directory existence).

## GUI
* Tauri-based desktop application that wraps the orchestrator.
* Loads task definitions from the `configs` directory and exposes them to the frontend.
* Executes tasks via commands such as `execute_task` and `list_tasks`.

## Development
Run `cargo test` to build and test the workspace. Some optional features (e.g., Julia
integration) require additional system dependencies.

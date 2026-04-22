
# System Architecture: Adaptive Expert Platform (Integrated)

---

This document provides a high-level overview of the fully integrated platform's architecture. The design prioritizes modularity and a polyglot approach, where a central Rust orchestrator manages a suite of specialized "expert" agents written in the best language for each task.

---

# 📊 Component Flow Diagram

```Generated mermaid

graph TD
    subgraph "User / Client"
        JsonRequest[JSON Task Request]
    end

    subgraph "Rust Orchestration Hub"
        JsonRequest --> Core(adaptive_expert_core)
        Core -- Manages --> Orchestrator
        Orchestrator <-->|mpsc channel| AgentTask(Agent Task)
        AgentTask -- dispatches to --> AgentImpl{Agent Trait Impl}
    end

    subgraph "Expert Agents (Connectors & Plugins)"
        AgentImpl --> JuliaExpert[Julia Expert Agent]
        AgentImpl --> PythonTool[Python Tool Agent]
        AgentImpl --> LlmAgent[LLM Agent]
        AgentImpl --> NativePlugin[Native Plugin Agent]
    end

    subgraph "External Runtimes & Libraries (The "Real" Experts)"
        JuliaExpert -->|jlrs FFI| JuliaRuntime[Julia Runtime + Models (.jl)]
        PythonTool -->|exec process| PythonRuntime[Python Runtime + Scripts (.py)]
        LlmAgent -->|llama_cpp crate| GgufModel[LLM Model (.gguf)]
        NativePlugin -->|libloading| SharedLib[Shared Library (.so/.dll)]
    end

    style Orchestrator fill:#89CFF0
    style AgentImpl fill:#90EE90
    style JuliaExpert fill:#9575CD,stroke:#333
    style PythonTool fill:#FFE082,stroke:#333
    style LlmAgent fill:#F06292,stroke:#333
    style NativePlugin fill:#FFAB91,stroke:#333
```

# 🧩 Component Breakdown

**Rust Orchestration Hub**: The core of the system, written in Rust and composed of several crates (e.g., adaptive_expert_core). Its Orchestrator receives tasks, validates them, and dispatches them to the appropriate registered agent via an asynchronous channel. It knows nothing about the internal logic of the agents, only how to call them.

**Expert Agents**: These are Rust structs that implement the Agent trait. They act as "connectors" or "adapters" that bridge the gap between the generic Rust hub and the specialized, often non-Rust, tools.

- **Julia Expert Agent**: A built-in Rust agent that uses the jlrs crate. Its sole purpose is to initialize the Julia runtime, load .jl model files (e.g., for Causal Inference, LTNs, CLIP), pass them JSON configuration, execute their functions, and return the results to the orchestrator.

- **Python Tool Agent**: A built-in Rust agent that executes Python scripts (.py) as external processes using tokio::process::Command. It captures the standard output and error, making tools like the PPTX converter and image montage creator available to the system.

- **LLM Agent**: A built-in Rust agent that uses the llama_cpp crate. It is responsible for loading a GGUF model file from disk, managing an inference session, and handling prompting and token generation.

- **Native Plugin Agent**: An agent loaded at runtime from a dynamic shared library (.so, .dll). This is the most performant integration path, ideal for high-throughput experts written in Rust, Zig, or C++. The DQN agent is a prime example of a native plugin.


**External Runtimes & Libraries**: These are the actual expert tools and models that perform the work. They are not part of the Rust codebase but are essential dependencies that must exist in the execution environment (e.g., inside the Docker container).

- **Julia Runtime**: A full installation of the Julia language, plus required packages like Flux.jl and CausalInference.jl.

- **Python Runtime**: A full installation of Python, plus required packages like numpy, Pillow, and python-pptx, and system dependencies like libreoffice.

- **GGUF Model**: A binary file containing the weights for a Large Language Model (e.g., Llama-3-8B-Instruct.Q4_K_M.gguf).

- **Shared Library**: The compiled output (.so/.dll) of a plugin crate, like libdqn_plugin.so.

# ⚙️ Workflow Example: Causal Inference Request

- A user sends a JSON request: {"agent": "julia_expert", "input": "{\"module\": \"causal\", \"config\": {...}}"}.

- The Orchestrator receives the task and finds the registered JuliaExpertAgent.

- The JuliaExpertAgent's handle method is called. It parses the input to see that the causal module is requested.

- The agent uses jlrs to start the Julia runtime, include() the causal_model.jl file, and call the run_causal_from_json function, passing the config string.

- The **Julia Runtime** executes the function, which uses the CausalInference.jl library to perform the actual statistical computation on data/health.csv.

- Julia returns a result string (e.g., a JSON object with the estimated effect) to the Rust agent.

- The Rust agent passes this result back to the Orchestrator, which completes the task and returns the final result to the user.

```This architecture creates a clean separation of concerns, allowing the Rust hub to be a stable, high-performance dispatcher while enabling rapid development and integration of expert tools in any language.```

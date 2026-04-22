# models/julia/causal_model.jl
using CSV, DataFrames, CausalInference, JSON

"""
Runs the causal effect estimation based on a JSON configuration string.
This is the main entry point for calls from the Rust orchestrator.
"""
function estimate_effect(cfg)
    required_keys = ["data_path", "graph", "treatment", "outcome"]
    for key in required_keys
        if !haskey(cfg, key)
            throw(ArgumentError("Missing required key in JSON config: $key"))
        end
    end

    df = CSV.read(cfg["data_path"], DataFrame)
    graph = read_dot(cfg["graph"])
    
    # The CausalInference.jl API is stateless, so we perform the estimation directly.
    model = causal_model(df, Symbol(cfg["treatment"]), Symbol(cfg["outcome"]), graph)
    est_value = estimate_effect(model, :backdoor)
    
    return Dict("status" => "success", "estimated_effect" => est_value)
end


function run_causal_from_json(json_config::String)
    try
        cfg = JSON.parse(json_config)
        action = get(cfg, "action", "estimate")

        result = if action == "estimate"
            estimate_effect(cfg)
        else
            throw(ArgumentError("Unknown action: '$action'. Must be 'estimate'."))
        end
        return JSON.json(result)
        
    catch e
        result = Dict(
            "status" => "error",
            "message" => sprint(showerror, e)
        )
        return JSON.json(result)
    end
end

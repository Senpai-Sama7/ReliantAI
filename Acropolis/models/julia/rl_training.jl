# models/julia/rl_training.jl
module RLTraining

using ReinforcementLearningEnvironments
using ReinforcementLearningCore
using Serialization
using JSON

# Model instances are now managed in a global dictionary to persist them between calls.
# In a multi-threaded server, this would require locks or a more robust cache.
const LOADED_MODELS = Dict{String, Any}()

"""
Create a new RL policy and store it in memory.
"""
function create_model(cfg)
    env = CartPoleEnv()
    # A placeholder for a more complex policy like DQNPolicy
    policy = RandomPolicy(action_space(env))
    model_id = get(cfg, "model_id", "default_rl_model")
    LOADED_MODELS[model_id] = (policy, env)
    return Dict("status" => "success", "message" => "RL model created.", "model_id" => model_id)
end

"""
Train an existing model instance.
"""
function train_model(cfg)
    model_id = get(cfg, "model_id", "default_rl_model")
    !haskey(LOADED_MODELS, model_id) && throw(ArgumentError("Model with ID '$model_id' not found."))
    
    policy, env = LOADED_MODELS[model_id]
    episodes = get(cfg, "episodes", 50)
    hook = TotalRewardPerEpisode()

    for i in 1:episodes
        run(policy, env, StopAfterStep(200), hook)
    end
    
    total_reward = sum(hook.rewards)
    avg_reward = total_reward / episodes

    return Dict("status" => "success", "action" => "train", "episodes" => episodes, "total_reward" => total_reward, "average_reward_per_episode" => avg_reward)
end

"""
Evaluate a model instance.
"""
function evaluate_model(cfg)
    model_id = get(cfg, "model_id", "default_rl_model")
    !haskey(LOADED_MODELS, model_id) && throw(ArgumentError("Model with ID '$model_id' not found."))
    
    policy, env = LOADED_MODELS[model_id]
    episodes = get(cfg, "episodes", 10)
    hook = TotalRewardPerEpisode()

    for i in 1:episodes
        run(policy, env, StopAfterStep(200), hook)
    end
    
    total_reward = sum(hook.rewards)
    avg_reward = total_reward / episodes

    return Dict("status" => "success", "action" => "evaluate", "episodes" => episodes, "total_reward" => total_reward, "average_reward_per_episode" => avg_reward)
end

"""
Save a model instance to a file.
"""
function save_model(cfg)
    model_id = get(cfg, "model_id", "default_rl_model")
    model_path = get(cfg, "model_path", "data/models/cartpole_policy.bson")
    !haskey(LOADED_MODELS, model_id) && throw(ArgumentError("Model with ID '$model_id' not found."))

    if !isdir(dirname(model_path))
        mkpath(dirname(model_path))
    end

    policy, _ = LOADED_MODELS[model_id]
    serialize(model_path, policy)
    return Dict("status" => "success", "message" => "Model '$model_id' saved to '$model_path'.")
end

"""
Load a model from a file into memory.
"""
function load_model(cfg)
    model_id = get(cfg, "model_id", "default_rl_model")
    model_path = get(cfg, "model_path", "data/models/cartpole_policy.bson")
    !isfile(model_path) && throw(ArgumentError("Model file not found at '$model_path'."))

    env = CartPoleEnv()
    policy = deserialize(model_path)
    LOADED_MODELS[model_id] = (policy, env)
    return Dict("status" => "success", "message" => "Model loaded from '$model_path' with ID '$model_id'.")
end


"""
Main entry point for the Rust orchestrator to interact with this RL module.
Dispatches to different functions based on the 'action' key in JSON config.
"""
function run_rl_from_json(json_config::String)
    try
        cfg = JSON.parse(json_config)
        action = get(cfg, "action", "train")

        result = if action == "create"
            create_model(cfg)
        elseif action == "train"
            train_model(cfg)
        elseif action == "evaluate"
            evaluate_model(cfg)
        elseif action == "save"
            save_model(cfg)
        elseif action == "load"
            load_model(cfg)
        else
            throw(ArgumentError("Unknown action: '$action'. Must be one of: create, train, evaluate, save, load."))
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

end # module RLTraining

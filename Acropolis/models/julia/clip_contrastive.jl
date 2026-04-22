# models/julia/clip_contrastive.jl
using Flux, Metalhead, Statistics, JSON, Serialization

mutable struct CLIPModel
    image_encoder::Chain
    text_encoder::Chain
    temp::Float32
end

const LOADED_MODELS = Dict{String, CLIPModel}()

function create_model(cfg)
    model_id = get(cfg, "model_id", "default_clip_model")
    text_vocab_size = get(cfg, "text_vocab_size", 10000)
    embedding_dim = get(cfg, "embedding_dim", 512)

    img_encoder = Chain(
        Conv((3,3), 3=>16, stride=2, pad=1, relu),
        BatchNorm(16), MaxPool((2,2)),
        Conv((3,3), 16=>32, stride=2, pad=1, relu),
        BatchNorm(32), MaxPool((2,2)),
        Flux.flatten, Dense(32*14*14, embedding_dim), relu
    )
    txt_encoder = Chain(Dense(text_vocab_size, embedding_dim), relu)
    
    model = CLIPModel(img_encoder, txt_encoder, 0.07f0)
    LOADED_MODELS[model_id] = model
    
    return Dict("status" => "success", "message" => "CLIP model created.", "model_id" => model_id)
end

function compute_loss(m::CLIPModel, images, texts)
    img_f = m.image_encoder(images)
    txt_f = m.text_encoder(texts)
    img_f = img_f ./ (norm.(eachcol(img_f))' .+ 1e-8)
    txt_f = txt_f ./ (norm.(eachcol(txt_f))' .+ 1e-8)
    logits = txt_f' * img_f / m.temp
    labels = 1:size(logits, 1)
    return (Flux.Losses.logitcrossentropy(logits, labels) + Flux.Losses.logitcrossentropy(logits', labels)) / 2
end

function train_model(cfg)
    model_id = get(cfg, "model_id", "default_clip_model")
    !haskey(LOADED_MODELS, model_id) && throw(ArgumentError("Model with ID '$model_id' not found."))

    model = LOADED_MODELS[model_id]
    epochs = get(cfg, "epochs", 50)
    lr = get(cfg, "lr", 0.001)
    batch_size = get(cfg, "batch_size", 32)
    vocab_size = size(model.text_encoder[1].weight, 2)
    
    # Dummy data generation
    images = rand(Float32, 224, 224, 3, batch_size)
    texts_indices = rand(1:vocab_size, batch_size)
    texts = Flux.onehotbatch(texts_indices, 1:vocab_size)
    
    opt = ADAM(lr)
    final_loss = 0.0

    println("Starting Multimodal (CLIP) training for $epochs epochs...")
    for epoch in 1:epochs
        grads = gradient(params(model.image_encoder, model.text_encoder)) do
            final_loss = compute_loss(model, images, texts)
            return final_loss
        end
        Flux.Optimise.update!(opt, params(model.image_encoder, model.text_encoder), grads)
        (epoch % 10 == 0 || epoch == 1) && println("Epoch: $epoch, Loss: $final_loss")
    end
    
    return Dict("status" => "success", "message" => "Multimodal training complete", "final_loss" => final_loss)
end

function save_model(cfg)
    model_id = get(cfg, "model_id", "default_clip_model")
    model_path = get(cfg, "model_path", "data/models/clip_model.bson")
    !haskey(LOADED_MODELS, model_id) && throw(ArgumentError("Model with ID '$model_id' not found."))

    !isdir(dirname(model_path)) && mkpath(dirname(model_path))
    serialize(model_path, LOADED_MODELS[model_id])
    
    return Dict("status" => "success", "message" => "Model '$model_id' saved to '$model_path'.")
end

function load_model(cfg)
    model_id = get(cfg, "model_id", "default_clip_model")
    model_path = get(cfg, "model_path", "data/models/clip_model.bson")
    !isfile(model_path) && throw(ArgumentError("Model file not found at '$model_path'."))

    LOADED_MODELS[model_id] = deserialize(model_path)
    return Dict("status" => "success", "message" => "Model loaded from '$model_path' with ID '$model_id'.")
end

"""
Main entry point for calls from the Rust orchestrator.
"""
function run_clip_from_json(json_config::String)
    try
        cfg = JSON.parse(json_config)
        action = get(cfg, "action", "train")

        result = if action == "create"
            create_model(cfg)
        elseif action == "train"
            train_model(cfg)
        elseif action == "save"
            save_model(cfg)
        elseif action == "load"
            load_model(cfg)
        else
            throw(ArgumentError("Unknown action: '$action'. Must be one of: create, train, save, load."))
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

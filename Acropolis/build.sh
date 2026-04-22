#!/usr/bin/env bash
set -e

IMAGE_NAME="adaptive-expert-platform"
CONTAINER_NAME="adaptive-expert-platform-container"
# Space-separated features, matching your Cargo.toml
FEATURES="--features \"llama julia\""
PLUGIN_DIR="plugins"

# Detect which mode to run (default to local if no argument given)
MODE=${1:-local}

echo "=== Adaptive Expert Platform Build Script ==="
echo "Mode selected: $MODE"
echo "--------------------------------------------"

if [ "$MODE" == "local" ]; then
    echo "🚀 Starting LOCAL build with Rust & plugins..."

    # Point jl-sys to your Julia install
    export JULIA_DIR="/opt/julia-1.11.1"

    echo "[1/5] Building Rust workspace with features: ${FEATURES}..."
    cargo build --release ${FEATURES}

    echo "[2/5] Ensuring plugin directory exists..."
    mkdir -p $PLUGIN_DIR

    echo "[3/5] Building dqn_plugin as a dynamic library..."
    cargo build --release -p dqn_plugin ${FEATURES}

    echo "[4/5] Detecting OS and copying plugin artifact..."
    PLUGIN_EXT=".so"
    case "$(uname -s)" in
        Darwin)   PLUGIN_EXT=".dylib"; echo "Detected macOS";;
        Linux)    PLUGIN_EXT=".so";    echo "Detected Linux";;
        MINGW*|CYGWIN*|MSYS*) PLUGIN_EXT=".dll"; echo "Detected Windows";;
        *)        echo "Warning: Unknown OS, defaulting to .so";;
    esac

    DQN_PLUGIN_NAME="libdqn_plugin$PLUGIN_EXT"
    SOURCE_PATH="target/release/$DQN_PLUGIN_NAME"
    DEST_PATH="$PLUGIN_DIR/$DQN_PLUGIN_NAME"

    if [ -f "$SOURCE_PATH" ]; then
        echo "Copying $DQN_PLUGIN_NAME to $DEST_PATH..."
        cp "$SOURCE_PATH" "$DEST_PATH"
    else
        echo "❌ Error: Compiled plugin not found at $SOURCE_PATH"
        exit 1
    fi

    echo "[5/5] Running tests..."
    cargo test --release ${FEATURES}

    echo "✅ Local Build & Tests Complete."
    echo "➡️ To run locally: cargo run --release ${FEATURES}"

elif [ "$MODE" == "docker" ]; then
    echo "🐳 Starting DOCKER build & run..."

    echo "[1/3] Building Docker image: $IMAGE_NAME..."
    docker build --no-cache -t $IMAGE_NAME .

    echo "[2/3] Stopping/removing any old container named $CONTAINER_NAME..."
    if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
        docker stop $CONTAINER_NAME >/dev/null 2>&1 || true
        docker rm   $CONTAINER_NAME >/dev/null 2>&1 || true
    fi

    echo "[3/3] Running container: $CONTAINER_NAME"
    docker run --rm -it \
        --name $CONTAINER_NAME \
        $IMAGE_NAME

    echo "✅ Docker build & run complete."

else
    echo "❌ Invalid mode: $MODE"
    echo "Usage: ./build.sh [local|docker]"
    exit 1
fi


# ============================
#  BUILDER STAGE
# ============================
FROM rust:1.81.0-slim-bookworm AS builder

# Create non-root user for build process
RUN groupadd -r builduser && useradd -r -g builduser builduser

# Install build-time dependencies for Rust + jlrs (minimal set)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        clang \
        libclang-dev \
        ca-certificates \
        wget \
        xz-utils \
        pkg-config \
        libssl-dev && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Download and install Julia with GPG signature verification
# Using Julia 1.9.4 LTS for stability and security
ENV JULIA_VERSION=1.9.4
ENV JULIA_DIR="/opt/julia-${JULIA_VERSION}"
ENV JULIA_GPG_KEY="3673DF529D9049477F76B37566E3C7DC03D6E495"

RUN apt-get update && apt-get install -y --no-install-recommends gnupg2 && \
    # Import Julia GPG key
    gpg --keyserver keyserver.ubuntu.com --recv-keys ${JULIA_GPG_KEY} && \
    # Download Julia tarball and signature
    wget -qO /tmp/julia.tar.gz \
      "https://julialang-s3.julialang.org/bin/linux/x64/1.9/julia-${JULIA_VERSION}-linux-x86_64.tar.gz" && \
    wget -qO /tmp/julia.tar.gz.asc \
      "https://julialang-s3.julialang.org/bin/linux/x64/1.9/julia-${JULIA_VERSION}-linux-x86_64.tar.gz.asc" && \
    # Verify GPG signature
    gpg --verify /tmp/julia.tar.gz.asc /tmp/julia.tar.gz && \
    # Extract and install
    tar -xzf /tmp/julia.tar.gz -C /opt && \
    ln -s "${JULIA_DIR}/bin/julia" /usr/local/bin/julia && \
    # Cleanup
    rm /tmp/julia.tar.gz /tmp/julia.tar.gz.asc && \
    apt-get remove -y gnupg2 && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* && \
    # Test Julia installation
    julia --version

# Set up secure build environment
WORKDIR /build
RUN chown builduser:builduser /build

# Switch to non-root user for build
USER builduser

# Copy dependency files first for better layer caching
COPY --chown=builduser:builduser Cargo.toml Cargo.lock ./
COPY --chown=builduser:builduser adaptive_expert_platform/Cargo.toml ./adaptive_expert_platform/
COPY --chown=builduser:builduser plugins/*/Cargo.toml ./plugins/*/

# Pre-build dependencies for better caching
RUN cargo fetch

# Copy source code
COPY --chown=builduser:builduser adaptive_expert_platform ./adaptive_expert_platform
COPY --chown=builduser:builduser plugins ./plugins

# Build with security-focused flags
ENV RUSTFLAGS="-C target-feature=+crt-static -C relocation-model=static"
RUN cargo build --release --features "llama julia" && \
    # Strip debug symbols to reduce binary size and remove build tools
    strip target/release/acropolis-cli && \
    # Clean up build artifacts and tools that shouldn't be in final image
    cargo clean && \
    rm -rf ~/.cargo/registry ~/.cargo/git

# ============================
#  RUNTIME STAGE
# ============================
FROM debian:12.8-slim AS runtime

# Security: Create non-root user for runtime
RUN groupadd -r acropolis && \
    useradd -r -g acropolis -s /sbin/nologin -c "Acropolis service user" acropolis

# Install minimal runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        ca-certificates \
        wget \
        xz-utils \
        libssl3 \
        openssl && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean && \
    # Remove package manager cache and unnecessary files
    rm -rf /var/cache/apt/* /var/log/* /tmp/* /var/tmp/*

# Install Julia runtime with GPG verification (same version as builder)
ENV JULIA_VERSION=1.9.4
ENV JULIA_DIR="/opt/julia-${JULIA_VERSION}"
ENV JULIA_GPG_KEY="3673DF529D9049477F76B37566E3C7DC03D6E495"

RUN apt-get update && apt-get install -y --no-install-recommends gnupg2 && \
    # Import Julia GPG key
    gpg --keyserver keyserver.ubuntu.com --recv-keys ${JULIA_GPG_KEY} && \
    # Download Julia tarball and signature
    wget -qO /tmp/julia.tar.gz \
      "https://julialang-s3.julialang.org/bin/linux/x64/1.9/julia-${JULIA_VERSION}-linux-x86_64.tar.gz" && \
    wget -qO /tmp/julia.tar.gz.asc \
      "https://julialang-s3.julialang.org/bin/linux/x64/1.9/julia-${JULIA_VERSION}-linux-x86_64.tar.gz.asc" && \
    # Verify GPG signature
    gpg --verify /tmp/julia.tar.gz.asc /tmp/julia.tar.gz && \
    # Extract and install
    tar -xzf /tmp/julia.tar.gz -C /opt && \
    ln -s "${JULIA_DIR}/bin/julia" /usr/local/bin/julia && \
    # Cleanup GPG and temporary files
    rm /tmp/julia.tar.gz /tmp/julia.tar.gz.asc && \
    apt-get remove -y gnupg2 && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/* && \
    julia --version

# Create application directories with proper permissions
RUN mkdir -p /app/{plugins,models,data,logs,config} && \
    chown -R acropolis:acropolis /app

# Copy compiled binary from builder
COPY --from=builder --chown=acropolis:acropolis /build/target/release/acropolis-cli /usr/local/bin/acropolis-cli

# Copy plugins and models
COPY --from=builder --chown=acropolis:acropolis /build/target/release/deps/*.so /app/plugins/
COPY --chown=acropolis:acropolis models /app/models/
COPY --chown=acropolis:acropolis configs /app/config/

# Set secure runtime configuration
WORKDIR /app

# Security: Switch to non-root user
USER acropolis

# Set environment variables for security
ENV RUST_BACKTRACE=1
ENV RUST_LOG=info
ENV AEP_PLUGIN_DIR=/app/plugins
ENV AEP_MODEL_DIR=/app/models
ENV AEP_DATA_DIR=/app/data

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD acropolis-cli --version || exit 1

# Security: Run with minimal privileges
EXPOSE 8080
EXPOSE 9090

# Default entrypoint with explicit path
ENTRYPOINT ["/usr/local/bin/acropolis-cli"]
CMD ["serve", "--addr", "0.0.0.0:8080"]

# Metadata for security scanning
LABEL maintainer="Adaptive Expert Platform Team"
LABEL version="0.1.0"
LABEL description="Adaptive Expert Platform - Secure Multi-Language AI Orchestrator"
LABEL org.opencontainers.image.source="https://github.com/adaptive-expert-platform/core"
LABEL org.opencontainers.image.licenses="MIT"
LABEL security.scan.enabled="true"

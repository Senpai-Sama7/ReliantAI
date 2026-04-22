# Warp Base Environment for HVAC AI Dispatch
# Builds on python:3.11-slim with essential build tools
FROM python:3.11-slim

# Prevent Python from buffering stdout/stderr and creating .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install essential build tools for native extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

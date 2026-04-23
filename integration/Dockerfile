FROM python:3.11-slim

WORKDIR /app

# Install system dependencies + curl for Docker health probes (AGENTS.md invariant)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared modules
COPY shared/ ./shared/

# Copy service integration modules
COPY services/ ./services/
COPY skill_integration.py .
COPY a2a_bridge.py .
COPY cross_system_orchestrator.py .
COPY intelligent_routing.py .
COPY hitl_optimizer.py .

# Copy metacognitive layer
COPY metacognitive_layer/ ./metacognitive_layer/

# Copy main entry point
COPY main.py .

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')"

# Run the service
CMD ["python", "main.py"]

# ════════════════════════════════════════════════════════════
# DOCKERFILE: Unified HVAC AI Dispatch + Premium Website
# Multi-agent FastAPI server with React frontend and SQLite.
# ════════════════════════════════════════════════════════════

# 1. Base Image: Python 3.11 Slim
FROM python:3.11-slim

# 2. Prevent Python from buffering stdout/stderr and creating .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Set Working Directory
WORKDIR /app

# 4. Install essential build deps + Node.js for frontend build
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    gnupg \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_20.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# 5. Copy Requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy and build frontend
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm ci

COPY frontend/ ./frontend/
RUN cd frontend && npm run build

# 7. Copy Application Source Code
COPY . .

# 8. Create directory for SQLite persistent data (Render mount point)
RUN mkdir -p /data && chmod 777 /data

# 9. Expose FastAPI Port
EXPOSE 8000

# 10. Healthcheck to ensure the container is truly healthy
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# 11. Default Launch Command (Uvicorn)
# Using uvicorn directly for production-grade ASGI serving.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

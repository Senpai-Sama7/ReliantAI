# Citadel — Security & Observability Service
# Flask + TimescaleDB backend

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies + curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY services/ ./services/
COPY scripts/ ./scripts/
COPY data/ ./data/
COPY desktop_gui.py ./
COPY local_agent/ ./local_agent/

# Set environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=backend/app.py \
    PORT=8100

# Expose port
EXPOSE 8100

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8100/api/health || exit 1

# Run with uvicorn (ASGI wrapper for Flask via Quart or pure Flask via gunicorn)
# app.py uses FastAPI actually, so use uvicorn
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8100", "--workers", "2"]

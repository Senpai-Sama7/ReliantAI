# DocuMancer — Document to AI-Optimized JSON Converter
# Python FastAPI backend

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies + curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tesseract-ocr \
    libtesseract-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/
COPY shared/ ./shared/
COPY assets/ ./assets/

# Set environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DOCUMANCER_HOST=0.0.0.0 \
    DOCUMANCER_PORT=8103 \
    DOCUMANCER_LOG_LEVEL=INFO

EXPOSE 8103

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8103/health || exit 1

CMD ["python", "-m", "uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "8103", "--workers", "2"]

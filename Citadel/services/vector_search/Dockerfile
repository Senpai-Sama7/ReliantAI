# syntax=docker/dockerfile:1.7
FROM python:3.11-slim AS builder

ENV PIP_DEFAULT_TIMEOUT=180 \
    PIP_RETRIES=10 \
    VIRTUAL_ENV=/app/venv \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/venv/bin:$PATH"

WORKDIR /app

# Create and prepare venv
RUN python -m venv $VIRTUAL_ENV && python -m pip install --upgrade pip

# Preinstall CPU-only PyTorch to avoid CUDA wheels during dependency resolution
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --index-url https://download.pytorch.org/whl/cpu torch==2.8.0

# Install Python deps (use BuildKit cache mount; do NOT use --no-cache-dir)
COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt

# Copy application code
COPY . .

# ---------- Runtime image ----------
FROM python:3.11-slim AS runtime

ENV VIRTUAL_ENV=/app/venv \
    PATH="/app/venv/bin:$PATH"

WORKDIR /app

COPY --from=builder /app/venv /app/venv
COPY --from=builder /app /app

EXPOSE 8000
# If your app module is different, change main:app accordingly
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


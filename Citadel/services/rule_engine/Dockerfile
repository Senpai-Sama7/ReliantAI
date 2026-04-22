# --- Builder Stage ---
FROM python:3.11-slim as builder

WORKDIR /app

RUN python3 -m venv /app/venv

COPY requirements.txt ./
RUN . /app/venv/bin/activate && \
    pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*

# --- Final Stage ---
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /app/venv ./venv
COPY main.py ./
COPY api_spec.yaml ./
COPY sample_data ./sample_data

EXPOSE 8000

CMD ["sh", "-c", ". venv/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8000"]
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y curl docker.io jq gcc && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser
RUN mkdir -p /app/data && chown -R appuser:appuser /app
EXPOSE 8004
USER appuser
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]

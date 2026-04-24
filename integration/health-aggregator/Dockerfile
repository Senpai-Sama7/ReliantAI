FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser
COPY . .
RUN chown -R appuser:appuser /app
EXPOSE 8086
USER appuser
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8086"]

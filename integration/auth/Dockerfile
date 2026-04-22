FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY auth_server.py .

# Health check
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Run
CMD ["python", "auth_server.py"]

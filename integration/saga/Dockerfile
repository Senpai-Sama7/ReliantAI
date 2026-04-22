FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY saga_orchestrator.py .

HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD python -c "import requests; r = requests.get('http://localhost:8090/health'); exit(0 if r.status_code == 200 else 1)"

CMD ["python", "saga_orchestrator.py"]

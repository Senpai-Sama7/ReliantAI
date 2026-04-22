FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY event_bus.py .

HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8081/health')"

CMD ["python", "event_bus.py"]

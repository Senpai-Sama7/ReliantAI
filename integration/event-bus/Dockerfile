FROM python:3.11-slim

WORKDIR /app

COPY event-bus/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ ./shared/
COPY event-bus/event_bus.py .

# Health check using httpx (installed dependency)
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD python -c "import httpx; r = httpx.get('http://localhost:8081/health'); exit(0 if r.status_code == 200 else 1)"

CMD ["python", "event_bus.py"]

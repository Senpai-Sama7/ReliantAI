FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

COPY integration/event-bus/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

COPY integration/shared/ /app/integration/shared/
COPY shared/ /app/shared/
COPY integration/event-bus/event_bus.py /app/integration/event-bus/event_bus.py

RUN chown -R appuser:appuser /app

WORKDIR /app/integration/event-bus

HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD curl -f http://localhost:8081/health

USER appuser
CMD ["python", "event_bus.py"]

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY integration/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ /tmp/shared_base/
COPY integration/shared/ /tmp/shared_integration/
RUN cp -a /tmp/shared_integration/. /app/shared/ && \
    cp -a /tmp/shared_base/. /app/shared/ && \
    rm -rf /tmp/shared_base /tmp/shared_integration

COPY integration/services/ ./services/
COPY integration/skill_integration.py .
COPY integration/a2a_bridge.py .
COPY integration/cross_system_orchestrator.py .
COPY integration/intelligent_routing.py .
COPY integration/hitl_optimizer.py .
COPY integration/metacognitive_layer/ ./metacognitive_layer/
COPY integration/main.py .

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8080/health

CMD ["python", "main.py"]

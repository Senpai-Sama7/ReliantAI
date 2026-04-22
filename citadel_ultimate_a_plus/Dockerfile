FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium

COPY . .

ENV CITADEL_DB_PATH=/app/workspace/state/lead_queue.db
EXPOSE 8888

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8888/health')" || exit 1

CMD ["python", "-m", "uvicorn", "dashboard_app:app", "--host", "0.0.0.0", "--port", "8888"]

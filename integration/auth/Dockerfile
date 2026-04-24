FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY auth/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

# Copy shared module
COPY shared/ ./shared/

# Copy auth module files
COPY auth/rate_limiter.py .
COPY auth/user_store.py .
COPY auth/auth_server.py .
COPY auth/migrate.py .
COPY auth/migrations/ ./migrations/

# Copy and set up entrypoint script
COPY auth/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
RUN chown -R appuser:appuser /app /app/entrypoint.sh

# Health check using httpx (installed dependency)
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD python -c "import httpx; r = httpx.get('http://localhost:8080/health'); exit(0 if r.status_code == 200 else 1)"

# Run
USER appuser
CMD ["/app/entrypoint.sh"]

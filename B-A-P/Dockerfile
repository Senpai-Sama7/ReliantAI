FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1

# system libs for pandas, matplotlib, postgres
RUN apt-get update && apt-get install -y \
  build-essential gcc libpq-dev curl git && \
  rm -rf /var/lib/apt/lists/*

# Poetry install
RUN pip install --no-cache-dir poetry==1.8.2

WORKDIR /app
COPY pyproject.toml poetry.lock* /app/
# README.md is optional; create a minimal one if missing to avoid build failure
RUN if [ ! -f README.md ]; then echo "# B-A-P" > README.md; fi

# Copy source before poetry install so the package can be installed
COPY src/ /app/src/
RUN poetry config virtualenvs.create false && \
  poetry install --no-interaction --no-ansi --only main

# uvicorn hot reload off for prod
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

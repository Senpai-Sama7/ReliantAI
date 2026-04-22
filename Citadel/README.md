# Citadel

Citadel is a modular collection of Python microservices and tools for building AI-powered applications. Each service is a FastAPI application secured with an API key and exposes a `/health` endpoint for basic monitoring.

## Services

### API Gateway

- Routes requests to downstream services based on the URL prefix and forwards the API key to each request.
- Provides a `/health` endpoint reporting gateway status.

### Vector Search Service

- Generates sentence embeddings with a configurable model and stores them in Redis via `redisvl`.
- `/index` loads documents into the vector index and `/search` retrieves similar documents by vector similarity.

### Knowledge Graph Service

- Wraps a Neo4j database and allows read‑only `MATCH` queries through the `/query` endpoint.

### Causal Inference Service

- Uses DoWhy to estimate treatment effects from tabular data via the `/effect` endpoint.

### Time Series Service

- Uses Facebook Prophet for forecasting and anomaly detection through `/forecast` and `/anomaly` endpoints.

### Multi‑Modal Service

- Generates deterministic embeddings for text or images and can search across mixed‑modality datasets using `/embed/text`, `/embed/image`, and `/search`.

### Hierarchical Classification Service

- Trains hierarchical classifiers and persists models to disk. `/train` returns a model identifier and `/predict` performs classification with a stored model.

### Rule Engine Service

- Evaluates sensor readings against Experta rules and returns matching actions via `/evaluate`.

### Orchestrator Service

- Listens for events on a Redis stream, dispatches them to other services, and persists results to Neo4j and TimescaleDB. `/publish` adds new events to the stream.

### Natural Language Agent Service

- Exposes an OpenAI-style `/v1/chat/completions` endpoint backed by Gemini.
- Can call downstream Citadel tools through the API gateway before returning a final answer.

## Development

### Setup

Before you begin, ensure you have Docker and Python installed.

1. **Create Environment File:** This project uses environment variables for configuration. Copy the example file to create your own local configuration:

   ```bash
   cp .env.example .env
   ```

   You **MUST** update the placeholder values in `.env` with secure credentials before starting services.

   ### Security & Credential Rotation

   **IMPORTANT:** The original `.env.example` inadvertently contained real deployment passwords which have now been removed. If you previously deployed using those passwords, you MUST rotate them:
   - **Neo4j (`NEO4J_PASSWORD`)**: Connect to your Neo4j instance as the `neo4j` user and run: `ALTER CURRENT USER SET PASSWORD FROM 'old_password' TO 'new_secure_password';`. Update `.env` and restart containers.
   - **TimescaleDB (`TS_PASSWORD`)**: Connect to Postgres as `postgres` or `tsdbadmin` and run: `ALTER USER tsdbadmin WITH PASSWORD 'new_secure_password';`. Update `.env` and restart containers.
   - **API_KEY**: Generate a new random 32-byte hex string (e.g., `openssl rand -hex 32`) and update the `.env` file of any service connecting to the Citadel Gateway.

2. **Start Services:** The project's infrastructure (Redis, Neo4j, etc.) is managed by Docker Compose. Start them in the background:

   ```bash
   docker compose up -d
   ```

3. **Install Dependencies:** Install the required Python packages:

   ```bash
   pip install -r requirements-dev.txt
   ```

### Linting

This project uses `pre-commit` for linting. Install the hooks and run them on all files:

```bash
pre-commit install
pre-commit run --all-files
```

### Testing

Once the services are running and dependencies are installed, run the test suite:

````bash
pytest
### Running Tests
The test suite exercises the major services. Running it requires dependencies such as Redis, Neo4j and the DoWhy library:

```bash
pytest
````

### Linting

Run the configured pre‑commit hooks before committing changes:

```bash
pre-commit run --files README.md
```

## Environment

Configuration is supplied through environment variables; an example is provided in `.env.example`.
`GEMINI_API_KEY` and `GEMINI_MODEL` configure the `services/nl_agent` runtime.

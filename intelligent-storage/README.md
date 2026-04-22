# Intelligent Storage Nexus

AI-powered file intelligence platform for teams and individuals who need to find, understand, and operate large file collections quickly and safely.

Intelligent Storage Nexus (ISN) turns file storage into a queryable knowledge system by combining:
- Semantic search with embeddings
- Keyword and metadata ranking
- Knowledge-graph traversal
- Natural-language filtering
- Real-time indexing control and observability
- Local-first operation with PostgreSQL + Ollama

---

## Table of Contents

- [Why It Matters](#why-it-matters)
- [Who It Is For](#who-it-is-for)
- [Capability Matrix](#capability-matrix)
- [Core Capabilities](#core-capabilities)
- [Real-World Use Cases and Value](#real-world-use-cases-and-value)
- [Product Tour for Non-Technical Users](#product-tour-for-non-technical-users)
- [Expert Quick Start](#expert-quick-start)
- [API Reference (Primary Endpoints)](#api-reference-primary-endpoints)
- [API Recipes (Copy/Paste)](#api-recipes-copypaste)
- [Configuration](#configuration)
- [Architecture Overview](#architecture-overview)
- [End-to-End Workflow](#end-to-end-workflow)
- [Testing and Verification](#testing-and-verification)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Security and Data Posture](#security-and-data-posture)
- [Roadmap Direction](#roadmap-direction)
- [License](#license)

---

## Why It Matters

Traditional file search fails when:
- Names are inconsistent
- Documentation is fragmented
- Duplicate or near-duplicate content grows silently
- Teams need operational controls, not just search boxes

ISN solves this by giving you meaning-based retrieval, graph context, and production-grade controls over indexing and system operations.

---

## Who It Is For

### Non-Technical Users

- Search with plain language like: `large python files from last week`
- Browse categorized files and previews
- Export results to CSV/JSON
- Get insights on duplicates, clusters, and anomalies

### Technical Teams and Experts

- Build automations on a complete REST + WebSocket API
- Blend semantic retrieval, RRF ranking, and graph traversal
- Control indexing jobs programmatically (start, pause, resume, stop)
- Monitor health, graph state, and optimization readiness

## Capability Matrix

| Capability | Non-Technical Value | Expert/Engineering Value | Where to Use |
| --- | --- | --- | --- |
| Natural-language search | Ask plain-English questions and get usable results quickly | Structured filters with deterministic parsing and LLM fallback | UI search, `POST /api/search/natural` |
| Hybrid and RRF retrieval | Better relevance than filename-only lookup | Weighted retrieval signals, rerank, optional graph enrichment | `POST /api/search/advanced`, `POST /api/search/v2` |
| Knowledge graph | Understand connected files and context | PageRank, communities, shortest-path analytics | `/api/graph/*` endpoints |
| Chat assistant (RAG) | Ask questions and get grounded answers from your own files | Streamed responses with history window and contextual retrieval | `POST /api/chat` |
| Insights and duplicates | Spot clutter, overlap, and anomalies | Duplicate forensics and extension clustering at scale | `POST /api/insights`, `GET /api/duplicates` |
| Progress-controlled indexing | See work status and ETA in real time | Trigger/pause/resume/stop operations programmatically | `/api/control/*`, `WS /ws/progress/{operation_id}` |
| Export and reporting | Share outputs with stakeholders | Pipe data into BI, scripts, and governance workflows | `GET /export/{export_type}` |
| Health and observability | Quick confidence check on system state | Service-level diagnostics and degraded-state visibility | `GET /api/health`, dashboard endpoints |

---

## Core Capabilities

### 1. File Intelligence and Indexing

- Recursive scan across configured mount points
- Metadata extraction: name, path, extension, size, MIME, modification time
- Content preview extraction for text-like files
- Rule-based tagging (language/framework/path heuristics)
- Content-aware chunking for code/docs
- Embedding generation (file-level + chunk-level)
- Optional knowledge-graph materialization (Apache AGE when available)

Indexer implementation: `indexer.py`

### 2. Search Stack

#### Advanced Hybrid Search
- Endpoint: `POST /api/search/advanced`
- Combines semantic, keyword, and metadata weighting
- Supports paging and cache-backed responses
- Uses optional optimization engine when available; falls back to PostgreSQL cleanly

#### RRF Search v2
- Endpoint: `POST /api/search/v2`
- Reciprocal Rank Fusion over:
  - Semantic vector results
  - Full-text keyword results
  - Metadata similarity
- Optional content-based reranking
- Optional related-file enrichment via graph neighbors

#### Semantic Search
- Endpoint: `POST /api/search/semantic`
- Pure vector similarity with threshold filtering

#### Faceted Search
- Endpoint: `POST /api/search/faceted`
- Filter by extensions and query terms with aggregate extension counts

#### Natural Language Search (Rules-First)
- Endpoint: `POST /api/search/natural`
- Deterministic parser handles:
  - File-type intent (`python`, `config`, `sql`, etc.)
  - Size constraints (`large`, `smaller than 50 kb`, etc.)
  - Relative/absolute dates (`last week`, `before 2025-01-01`)
  - Sort intent (`largest`, `newest`, `alphabetical`)
- Falls back to LLM parsing for ambiguous requests

### 3. Knowledge Graph Intelligence

- Neighborhood query from file id or file path
- Graph backend status and build metrics
- PageRank, community detection, shortest-path exploration
- Apache AGE preferred, NetworkX fallback with non-blocking background build

Key endpoints:
- `POST /api/graph/query`
- `GET /api/graph/status`
- `GET /api/graph/pagerank`
- `GET /api/graph/communities`
- `GET /api/graph/path`

### 4. RAG Chat Assistant

- Endpoint: `POST /api/chat`
- Streams RAG responses from indexed file context
- Uses chunk-level retrieval when available for finer grounding
- Supports conversational history window and contextual continuity

Chat implementation: `chat_service.py`

### 5. Insights, Recommendations, and Duplicate Detection

- Insights: `POST /api/insights`
  - Duplicate groups
  - Extension clusters
  - Size anomalies
- Recommendations: `POST /api/recommendations`
- Duplicates dashboard API: `GET /api/duplicates?type=exact|near`

### 6. Operations and Orchestration

- Trigger indexing jobs via API
- Track operation progress with ETA and status updates
- Pause/resume/stop long-running operations
- Real-time progress streams via WebSocket
- Clear metadata DB and fetch system stats

Control endpoints:
- `POST /api/control/index`
- `POST /api/control/clear-db`
- `GET /api/control/stats`
- `POST /api/control/progress/{operation_id}`
- `POST /api/control/stop/{operation_id}`
- `POST /api/control/pause/{operation_id}`
- `POST /api/control/resume/{operation_id}`
- `WS /ws/progress/{operation_id}`

### 7. Real-Time and Health Monitoring

- System health endpoint with service-level details
- Graph build state included in health response
- WebSocket search ping and quick semantic results

Endpoints:
- `GET /api/health`
- `WS /ws`

### 8. Optimization Engine Integration

- Detects and reports optional optimization modules
- Supports explicit indexing into optimization backend
- Includes performance benchmark endpoint

Endpoints:
- `GET /api/optimization/status`
- `POST /api/optimization/index`
- `POST /api/optimization/benchmark`

---

## Real-World Use Cases and Value

### Engineering Organizations
- Find implementation precedents across large codebases
- Identify duplicate configs/scripts to reduce drift
- Trace conceptual relationships between modules through graph links

### Security and Compliance Teams
- Locate sensitive or policy-relevant files faster
- Surface duplicate artifacts that increase exposure risk
- Export targeted inventories for audits

### Research and Knowledge Ops
- Retrieve semantically similar papers/notes/specs
- Build linked context around concepts, not just filenames
- Accelerate synthesis across large archives

### IT and Platform Operations
- Monitor indexing jobs and operational health in real time
- Programmatically orchestrate reindexing after migrations or storage changes
- Track system performance and storage conditions

---

## Product Tour for Non-Technical Users

### 10-Minute Guided Workflow

1. Start ISN with `./start.sh`.
2. Open `http://localhost:8000`.
3. In search, ask a plain-language question:
   - `show me recent configuration files`
   - `largest markdown files from last month`
   - `python files updated this week`
4. Narrow results with extensions, categories, and sorting.
5. Open file previews to confirm relevance.
6. Export the filtered list as CSV/JSON when you need to share findings.

### What You Can Do Without Writing Code

- Build a clean inventory of files by type, size, and recency
- Detect duplicate or near-duplicate content
- Review relationships between files in the graph view
- Ask the assistant to summarize context from indexed files
- Track indexing progress and ETA in real time

### If Search Results Look Sparse

- Trigger indexing from the UI quick actions or ask an admin to run `POST /api/control/index`.
- Wait for progress completion (`WS /ws/progress/{operation_id}`).
- Retry the same natural-language query.

---

## Expert Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL with `pgvector` and `pg_trgm`
- Ollama with embedding model available
- Optional:
  - Apache AGE extension for Cypher backend
  - Redis for distributed caching
  - Gunicorn for multi-worker deployment

### Install

```bash
pip install -r requirements.txt
```

Depending on environment, you may also need:

```bash
pip install asyncpg httpx slowapi psutil gunicorn redis
```

### Initialize Database

```bash
PGPASSWORD=storage_local_2026 psql -h localhost -p 5433 -U storage_admin -d intelligent_storage -f schema.sql
```

### Run

```bash
# Recommended (Gunicorn wrapper)
./start.sh

# API only
python3 api_server.py

# Indexer only
python3 indexer.py

# Web UI helper app
python3 web_ui.py
```

---

## API Reference (Primary Endpoints)

| Area | Method | Endpoint | Purpose |
|---|---|---|---|
| Search | POST | `/api/search/advanced` | Hybrid weighted search with paging |
| Search | POST | `/api/search/v2` | RRF + rerank + optional graph context |
| Search | POST | `/api/search/semantic` | Pure vector search |
| Search | POST | `/api/search/faceted` | Facet-based filtered search |
| Search | POST | `/api/search/natural` | Rules-first NL query parser |
| Chat | POST | `/api/chat` | Streaming RAG assistant |
| Graph | POST | `/api/graph/query` | File neighborhood and graph context |
| Graph | GET | `/api/graph/status` | Graph backend/build metrics |
| Graph | GET | `/api/graph/pagerank` | Importance ranking |
| Graph | GET | `/api/graph/communities` | Community detection |
| Graph | GET | `/api/graph/path` | Shortest path between files |
| Files | GET | `/api/files` | Paginated listing + q/category filters |
| Files | GET | `/api/files/{file_id}` | Full file metadata |
| Files | GET | `/api/files/{file_id}/content` | Content preview |
| Files | POST | `/api/files/{file_id}/tags` | Replace tag set |
| Insights | POST | `/api/insights` | Duplicate/cluster/anomaly insights |
| Recs | POST | `/api/recommendations` | Context-based recommendations |
| Ops | GET | `/api/dashboard` | Dashboard metrics |
| Ops | GET | `/api/duplicates` | Exact and near duplicate detection |
| Ops | GET | `/api/health` | Service health summary |
| Export | GET | `/export/{export_type}` | JSON/CSV export |

Full interactive docs when running:
- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`

### Complete Endpoint Catalog

| Method | Endpoint | Notes |
|---|---|---|
| GET | `/` | Serves `index.html` if present |
| POST | `/api/search/advanced` | Weighted hybrid search with optional optimization backend |
| POST | `/api/search/v2` | RRF + rerank + graph enrichment |
| POST | `/api/search/semantic` | Vector-only search |
| POST | `/api/search/faceted` | Faceted filtering and aggregations |
| POST | `/api/search/natural` | Rules-first NL parsing with LLM fallback |
| POST | `/api/chat` | Streaming RAG chat |
| POST | `/api/tot/reason` | Tree-of-Thoughts style exploratory reasoning |
| POST | `/api/graph/query` | Neighborhood query by id/path |
| GET | `/api/graph/status` | Graph backend/build metrics |
| GET | `/api/graph/pagerank` | Top connected files |
| GET | `/api/graph/communities` | Community detection |
| GET | `/api/graph/path` | Shortest path by ids |
| POST | `/api/insights` | Duplicates/clusters/anomalies |
| POST | `/api/recommendations` | Similarity-based file recommendations |
| GET | `/api/dashboard` | Aggregate storage/index statistics |
| GET | `/api/files` | List with query/category/extension/sort/paging |
| GET | `/api/files/{file_id}` | File metadata + tags |
| GET | `/api/files/{file_id}/content` | File preview content |
| POST | `/api/files/{file_id}/tags` | Replace file tags |
| GET | `/export/{export_type}` | Export search/files/insights/graph in JSON or CSV |
| WS | `/ws` | Ping and real-time search mini channel |
| GET | `/api/optimization/status` | Optimization module availability/capabilities |
| POST | `/api/optimization/index` | Push selected vectors into optimization engine |
| POST | `/api/optimization/benchmark` | Benchmark optimization path |
| GET | `/api/health` | Health and service status (can return 503 degraded) |
| GET | `/api/duplicates` | `type=exact|near` duplicate analysis |
| POST | `/api/control/index` | Start indexer subprocess with operation tracking |
| POST | `/api/control/clear-db` | Destructive metadata reset |
| GET | `/api/control/stats` | File/chunk/embedding/db-size stats |
| POST | `/api/control/progress/{operation_id}` | Internal progress reporting endpoint |
| POST | `/api/control/stop/{operation_id}` | Stop operation process tree |
| POST | `/api/control/pause/{operation_id}` | Pause operation process |
| POST | `/api/control/resume/{operation_id}` | Resume paused operation |
| WS | `/ws/progress/{operation_id}` | Operation progress stream |

## API Recipes (Copy/Paste)

### 1. Advanced Hybrid Search

```bash
curl -X POST http://localhost:8000/api/search/advanced \
  -H "Content-Type: application/json" \
  -d '{
    "query": "react authentication middleware",
    "semantic_weight": 0.6,
    "keyword_weight": 0.3,
    "meta_weight": 0.1,
    "page": 1,
    "limit": 20
  }'
```

### 2. Natural Language Search

```bash
curl -X POST http://localhost:8000/api/search/natural \
  -H "Content-Type: application/json" \
  -d '{"query":"large python files from last week","limit":25}'
```

### 3. Graph Neighborhood Query

```bash
curl -X POST http://localhost:8000/api/graph/query \
  -H "Content-Type: application/json" \
  -d '{"center_file_id": 1000, "depth": 2, "min_similarity": 0.6}'
```

### 4. Streaming RAG Chat

```bash
curl -N -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query":"Summarize auth flow and related config files",
    "history": [],
    "context_window": 5
  }'
```

### 5. Start and Track Indexing with Control API

```bash
# Start indexing
curl -X POST http://localhost:8000/api/control/index \
  -H "Content-Type: application/json" \
  -d '{"force": false}'

# Then subscribe for progress in your client
# WS: ws://localhost:8000/ws/progress/<operation_id>
```

### 6. Detect Near-Duplicates

```bash
curl "http://localhost:8000/api/duplicates?type=near&threshold=0.95&limit=50"
```

---

## Configuration

Core environment variables (see `config.py`):

### Database
- `ISN_DB_HOST` (default `localhost`)
- `ISN_DB_PORT` (default `5433`)
- `ISN_DB_NAME` (default `intelligent_storage`)
- `ISN_DB_USER` (default `storage_admin`)
- `ISN_DB_PASS` (default `storage_local_2026`)

### Embeddings / LLM
- `ISN_OLLAMA_URL` (default `http://localhost:11434/api/embed`)
- `ISN_EMBED_MODEL` (default `nomic-embed-text`)
- `ISN_EMBED_DIM` (default `768`)

### Tree of Thoughts (Reasoning Controls)
- `ISN_TOT_MAX_DEPTH` (default `3`)
- `ISN_TOT_BRANCHING_FACTOR` (default `3`)
- `ISN_TOT_SIMILARITY_THRESHOLD` (default `0.75`)

### Indexer
- `ISN_BATCH_SIZE` (default `32`)
- `ISN_TEXT_PREVIEW_LEN` (default `500`)
- `ISN_MAX_EMBED_TEXT` (default `2000`)
- `ISN_SCAN_PATHS_JSON` (JSON map of path -> partition)

Example:

```bash
export ISN_SCAN_PATHS_JSON='{"/data/projects":"DATA_HUB","/data/archive":"ARCHIVE"}'
```

### Graph Fallback Tuning
- `ISN_GRAPH_NODE_LIMIT` (default `5000`)
- `ISN_GRAPH_EMBED_LIMIT` (default `1000`)
- `ISN_GRAPH_EDGE_WINDOW` (default `10`)
- `ISN_GRAPH_EDGE_SIM_THRESHOLD` (default `0.85`)
- `ISN_GRAPH_QUERY_WAIT_TIMEOUT_SEC` (default `5.0`)

### API Governance
- `ISN_CORS_ORIGINS`
- `ISN_RATE_LIMIT_SEARCH` (default `30/minute`)
- `ISN_RATE_LIMIT_READ` (default `100/minute`)

### Deployment Profiles

- Local workstation:
  - Use defaults, run `./start.sh`, and point browser to `http://localhost:8000`.
- Shared internal server:
  - Set strict `ISN_CORS_ORIGINS`, keep rate limits enabled, and run behind an internal reverse proxy.
- Large indexing window:
  - Increase graph/index limits gradually and monitor `/api/health` + `/api/control/stats` during ingestion.

---

## Architecture Overview

```text
Web UI / Clients
    |
FastAPI API Layer (search, graph, chat, control, export)
    |
+-----------------------------+
| PostgreSQL + pgvector + FTS |
+-----------------------------+
    |
Indexer Pipeline (scan, chunk, embed, tag)
    |
Ollama (embeddings + chat)
```

Graph layer:
- Apache AGE when available
- NetworkX fallback with background build and status metrics

Caching layer:
- Redis preferred
- In-memory fallback with bounded pruning

---

## End-to-End Workflow

1. Configure scan paths and DB/LLM connection.
2. Run `python3 indexer.py` (or trigger `POST /api/control/index`).
3. Query with:
   - advanced hybrid search
   - RRF search
   - natural-language search
4. Explore relationships via graph endpoints.
5. Use chat assistant for context-grounded question answering.
6. Export and operationalize results.

---

## Testing and Verification

### Syntax and basic integrity

```bash
python3 -m py_compile api_server.py indexer.py web_ui.py graph_manager.py cache.py db.py config.py
```

### API smoke checks

```bash
curl http://localhost:8000/api/health
curl -X POST http://localhost:8000/api/search/advanced \
  -H "Content-Type: application/json" \
  -d '{"query":"React authentication","limit":5}'
curl -X POST http://localhost:8000/api/graph/query \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Systematic regression suite

```bash
python3 -m unittest -v tests/test_api_regression.py
```

Optional overrides:

```bash
ISN_TEST_BASE_URL=http://localhost:8000 \
ISN_TEST_TIMEOUT_SEC=30 \
python3 -m unittest -v tests/test_api_regression.py
```

---

## Troubleshooting

### `/api/health` returns 503

This can be expected when status is `degraded` (for example low disk free space warning). The payload contains service-level details in `detail.services`.

### Search returns empty results

- Ensure indexing has completed.
- Verify Ollama embedding endpoint and model availability.
- Check that `file_embeddings` has rows.

### Graph endpoints seem sparse

- Query `GET /api/graph/status`.
- Confirm graph built state and limits.
- Increase graph limits via env vars if needed.

### Chat endpoint issues

- Ensure chat model is available in Ollama.
- Verify `chat_service.py` dependencies and connectivity.

### Indexing won’t start from control endpoint

- Check process permissions for spawned subprocesses.
- Check API logs for `/api/control/index` errors.

---

## FAQ

### Is this only for developers?
No. Non-technical users can run natural-language searches, inspect previews, and export results directly from the UI without writing queries.

### Can I run this fully on-prem and offline?
Yes. ISN is designed for self-hosted/local-first operation. Keep PostgreSQL and Ollama on internal infrastructure to avoid external data transfer.

### What is the difference between `advanced`, `v2`, and `natural` search?
- `advanced`: weighted hybrid retrieval with semantic + keyword + metadata scoring.
- `v2`: RRF fusion plus optional rerank and graph-neighbor enrichment.
- `natural`: plain-language parser that generates deterministic filters (with LLM fallback when ambiguous).

### How do I know whether indexing is complete?
Use the operation ID returned by `POST /api/control/index` and subscribe to `WS /ws/progress/{operation_id}` for live completion state.

### What if Apache AGE is unavailable?
Graph functionality continues via NetworkX fallback. Use `GET /api/graph/status` to inspect active backend and build state.

### How do I export results for audits or reporting?
Use `GET /export/{export_type}?format=csv` or `format=json` for machine-readable handoff.

---

## Security and Data Posture

- Designed for local/self-hosted operation.
- Data remains in your PostgreSQL storage and local file systems unless you route services externally.
- Configure CORS and rate limits for your environment.
- Review API access controls before exposing outside trusted networks.

---

## Roadmap Direction

- Stronger authn/authz and multi-tenant controls
- Enhanced policy governance and data classification
- Expanded ingestion connectors and richer graph semantics
- Additional benchmarking + SLO instrumentation

---

## License

MIT (see repository license file if present).

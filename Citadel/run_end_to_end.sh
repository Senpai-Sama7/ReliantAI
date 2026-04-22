#!/usr/bin/env bash
set -euo pipefail

# -------- Config (override via env) --------
GATEWAY_PORT="${GATEWAY_PORT:-8010}"   # host port for API Gateway
NL_PORT="${NL_PORT:-8012}"             # host port for nl_agent
WAIT_SECS="${WAIT_SECS:-120}"          # how long to wait for readiness

BASE="http://localhost:${GATEWAY_PORT}"
NL="http://localhost:${NL_PORT}"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source ./.env
  set +a
fi

if [ -z "${API_KEY:-}" ]; then
  echo "[ERROR] API_KEY must be set in the environment or .env before running smoke tests."
  exit 1
fi

echo "[INFO] Starting services via docker compose..."
docker compose up -d

echo "[INFO] Waiting for services to become ready (up to ${WAIT_SECS}s)..."
deadline=$(( $(date +%s) + WAIT_SECS ))
code="000"
while [ "$(date +%s)" -lt "$deadline" ]; do
  # Gateway readiness = /docs returns 200
  code=$(curl -s -o /dev/null -w "%{http_code}" "${BASE}/docs")
  if [ "$code" = "200" ]; then
    echo "[INFO] API gateway is reachable at ${BASE} (docs OK)."
    break
  fi
  sleep 2
done

if [ "$code" != "200" ]; then
  echo "[ERROR] API gateway not ready. Last HTTP code: ${code}"
  docker ps
  echo "[HINT] Check logs: docker logs full_ai_platform-api_gateway"
  exit 1
fi

# ---------- Smoke tests ----------
set -x

# 1) Web Service via Gateway: /web/search  (POST)
#    Base URL and endpoint per Instruction Manual. 
curl -sS -X POST "${BASE}/web/search" \
  -H "X-API-KEY: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"query":"quick readiness check", "max_results": 1}' | jq . >/dev/null

# 2) Vector Search via Gateway: index a tiny doc, then search it.
curl -sS -X POST "${BASE}/vector/index" \
  -H "X-API-KEY: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"documents":[{"id":"doc_smoke_1","text":"The quick brown fox jumps over the lazy dog."}]}' | jq . >/dev/null

curl -sS -X POST "${BASE}/vector/search" \
  -H "X-API-KEY: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"query":"brown fox", "top_k": 1}' | jq . >/dev/null

# 3) NL Agent chat (OpenAI-compatible shape, Gemini-backed) at /v1/chat/completions (POST)
#    Non-streaming for simplicity.
curl -sS -X POST "${NL}/v1/chat/completions" \
  -H "X-API-KEY: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
        "model":"gemini-2.5-flash",
        "messages":[
          {"role":"system","content":"You are a helpful assistant that can use tools."},
          {"role":"user","content":"Say hello. One short sentence."}
        ],
        "stream": false
      }' | jq . >/dev/null

set +x
echo "[INFO] Smoke tests OK."
echo "[INFO] Explore APIs at ${BASE}/docs"
echo "[INFO] Talk to the agent at ${NL}/v1/chat/completions"

exit 0

#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# ReliantAI Platform — OpenAPI Client SDK Generation
# ═══════════════════════════════════════════════════════════════════════
#
# Usage:
#   ./scripts/generate-sdks.sh [output_dir]
#
# Generates typed client SDKs for all FastAPI services from their /openapi.json
# specs using the OpenAPI Generator Docker image.
#
# Supported languages: python, typescript-axios, go, java
# Default output: ./sdks/
#
# Prerequisites:
#   - Docker running
#   - Services must be accessible (run locally or point to staging)
#   - OPENAPI_GENERATOR_IMAGE=openapitools/openapi-generator-cli:latest

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
OUTPUT_DIR="${1:-$PROJECT_ROOT/sdks}"
GENERATOR_IMAGE="${OPENAPI_GENERATOR_IMAGE:-openapitools/openapi-generator-cli:latest}"

# Service endpoints (must expose /openapi.json when running)
# In CI, these are the internal Docker hostnames + ports
# Locally, use localhost after `docker compose up`
declare -A SERVICES=(
    [money]="http://localhost:8000"
    [complianceone]="http://localhost:8001"
    [finops360]="http://localhost:8002"
    [orchestrator]="http://localhost:9000"
    [integration]="http://localhost:8080"
)

# Languages to generate
LANGUAGES=(python typescript-axios)

log_info()  { echo "[INFO]  $*"; }
log_warn()  { echo "[WARN]  $*"; }
log_error() { echo "[ERROR] $*"; }

mkdir -p "$OUTPUT_DIR"

for SERVICE in "${!SERVICES[@]}"; do
    BASE_URL="${SERVICES[$SERVICE]}"
    SPEC_URL="${BASE_URL}/openapi.json"

    log_info "Fetching OpenAPI spec for ${SERVICE} from ${SPEC_URL}..."

    # Fetch spec (with retry)
    SPEC_FILE="$OUTPUT_DIR/${SERVICE}-openapi.json"
    if ! curl -sfL --retry 3 --retry-delay 5 "$SPEC_URL" -o "$SPEC_FILE" 2>/dev/null; then
        log_warn "Could not fetch spec for ${SERVICE}. Skipping."
        rm -f "$SPEC_FILE"
        continue
    fi

    # Validate JSON
    if ! python3 -m json.tool "$SPEC_FILE" > /dev/null 2>&1; then
        log_warn "Invalid JSON spec for ${SERVICE}. Skipping."
        rm -f "$SPEC_FILE"
        continue
    fi

    for LANG in "${LANGUAGES[@]}"; do
        OUT_PATH="$OUTPUT_DIR/${LANG}/${SERVICE}"
        mkdir -p "$OUT_PATH"

        log_info "Generating ${LANG} SDK for ${SERVICE}..."

        docker run --rm \
            -v "$SPEC_FILE:/spec.json:ro" \
            -v "$OUT_PATH:/out" \
            "$GENERATOR_IMAGE" generate \
            -i /spec.json \
            -g "$LANG" \
            -o /out \
            --additional-properties=packageName="reliantai_${SERVICE//-/_}" \
            --additional-properties=projectName="reliantai-${SERVICE}" \
            --additional-properties=packageVersion="$(date +%Y.%m.%d)" \
            > "$OUTPUT_DIR/${SERVICE}-${LANG}.log" 2>&1 || {
                log_warn "SDK generation failed for ${SERVICE}/${LANG}. See ${OUTPUT_DIR}/${SERVICE}-${LANG}.log"
                continue
            }

        log_info "Generated ${LANG} SDK for ${SERVICE} → ${OUT_PATH}"
    done
done

# Package SDKs for distribution
log_info "Packaging SDKs..."
cd "$OUTPUT_DIR"
for LANG in "${LANGUAGES[@]}"; do
    if [ -d "$LANG" ]; then
        tar czf "reliantai-sdks-${LANG}-$(date +%Y%m%d-%H%M%S).tar.gz" "$LANG"
        log_info "Packaged: reliantai-sdks-${LANG}-$(date +%Y%m%d-%H%M%S).tar.gz"
    fi
done

log_info "=== SDK Generation Complete ==="
log_info "Output directory: ${OUTPUT_DIR}"
log_info "Packages:"
ls -la "$OUTPUT_DIR"/*.tar.gz 2>/dev/null || true

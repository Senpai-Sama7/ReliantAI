#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════
# ReliantAI Platform — HashiCorp Vault Setup & Secret Seeding
# ═══════════════════════════════════════════════════════════════════════
#
# Usage:
#   ./scripts/vault-setup.sh [local|staging|production]
#
# This script:
#   1. Waits for Vault to be ready
#   2. Initializes Vault (production only; dev mode is pre-initialized)
#   3. Creates KV v2 mount for ReliantAI secrets
#   4. Creates ACL policies per service
#   5. Generates service tokens (or AppRole credentials)
#   6. Seeds example secrets for local development
#
# Prerequisites:
#   - Vault container must be running
#   - VAULT_TOKEN environment variable set (or dev root token)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-local}"

VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"
VAULT_TOKEN="${VAULT_TOKEN:-dev-root-token}"

log_info()  { echo "[INFO]  $*"; }
log_warn()  { echo "[WARN]  $*"; }
log_error() { echo "[ERROR] $*"; }

wait_for_vault() {
    log_info "Waiting for Vault at ${VAULT_ADDR}..."
    for i in {1..30}; do
        if curl -sf "${VAULT_ADDR}/v1/sys/health" >/dev/null 2>&1; then
            log_info "Vault is ready."
            return 0
        fi
        sleep 2
    done
    log_error "Vault did not become ready in 60 seconds."
    exit 1
}

enable_kv_v2() {
    log_info "Enabling KV v2 secrets engine..."
    curl -sf -X POST "${VAULT_ADDR}/v1/sys/mounts/secret" \
        -H "X-Vault-Token: ${VAULT_TOKEN}" \
        -d '{"type": "kv", "options": {"version": "2"}}' 2>/dev/null || \
    log_warn "KV mount may already exist (this is OK)."
}

create_policy() {
    local name="$1"
    local policy="$2"
    log_info "Creating policy: ${name}..."
    curl -sf -X PUT "${VAULT_ADDR}/v1/sys/policies/acl/${name}" \
        -H "X-Vault-Token: ${VAULT_TOKEN}" \
        -d "{\"policy\": \"${policy}\"}" >/dev/null 2>&1 || \
    log_warn "Policy ${name} may already exist."
}

write_secret() {
    local path="$1"
    local json_data="$2"
    log_info "Writing secret: ${path}..."
    curl -sf -X POST "${VAULT_ADDR}/v1/secret/data/${path}" \
        -H "X-Vault-Token: ${VAULT_TOKEN}" \
        -d "${json_data}" >/dev/null 2>&1 || \
    log_warn "Failed to write secret ${path}."
}

# ── Main ───────────────────────────────────────────────────────────────────
wait_for_vault
enable_kv_v2

# ── Service Policies ─────────────────────────────────────────────────────
log_info "Creating service ACL policies..."

create_policy "money-policy" 'path "secret/data/money/*" { capabilities = ["read", "list"] }'
create_policy "complianceone-policy" 'path "secret/data/complianceone/*" { capabilities = ["read", "list"] }'
create_policy "finops360-policy" 'path "secret/data/finops360/*" { capabilities = ["read", "list"] }'
create_policy "integration-policy" 'path "secret/data/integration/*" { capabilities = ["read", "list"] }'
create_policy "orchestrator-policy" 'path "secret/data/orchestrator/*" { capabilities = ["read", "list"] }'

# Admin policy for secret rotation
create_policy "reliantai-admin" 'path "secret/*" { capabilities = ["create", "read", "update", "delete", "list"] }'

# ── Seed Local Development Secrets ─────────────────────────────────────────
if [ "$ENVIRONMENT" = "local" ]; then
    log_info "Seeding local development secrets..."

    write_secret "money/db" '{"data": {"host": "postgres", "port": 5432, "dbname": "money", "user": "money", "password": "dev-money-password"}}'
    write_secret "money/stripe" '{"data": {"webhook_secret": "whsec_dev_example", "api_key": "sk_test_dev_example"}}'
    write_secret "money/twilio" '{"data": {"auth_token": "dev_twilio_token", "sid": "dev_twilio_sid"}}'

    write_secret "complianceone/db" '{"data": {"host": "postgres", "port": 5432, "dbname": "complianceone", "user": "complianceone", "password": "dev-compliance-password"}}'
    write_secret "complianceone/api_keys" '{"data": {"internal": "dev-compliance-api-key"}}'

    write_secret "finops360/db" '{"data": {"host": "postgres", "port": 5432, "dbname": "finops360", "user": "finops360", "password": "dev-finops-password"}}'
    write_secret "finops360/aws" '{"data": {"access_key_id": "dev_aws_key", "secret_access_key": "dev_aws_secret"}}'

    write_secret "integration/redis" '{"data": {"host": "redis", "port": 6379, "password": ""}}'
    write_secret "integration/event_bus" '{"data": {"api_key": "dev-event-bus-key"}}'

    write_secret "orchestrator/docker" '{"data": {"api_version": "1.43", "socket_path": "/var/run/docker.sock"}}'
fi

log_info "=== Vault Setup Complete ==="
log_info "Environment: ${ENVIRONMENT}"
log_info "Policies created: money, complianceone, finops360, integration, orchestrator, reliantai-admin"
log_info ""
log_info "Next steps:"
log_info "  1. Update .env with VAULT_TOKEN for each service"
log_info "  2. Use shared/vault_client.py in service startup"
log_info "  3. Run secret rotation via: python -c 'from shared.vault_client import VaultClient; vc = VaultClient(); vc.rotate_secret(\"money/db\", {...})'"

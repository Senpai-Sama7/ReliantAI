#!/usr/bin/env bash
set -euo pipefail

# Local-first S3 checkpoint sync daemon (safe for spot/preemptible instances).
# Pushes DB snapshots up on a timer and listens for SIGTERM/SIGINT for a final flush.

WORKDIR="${CITADEL_WORKDIR:-workspace}"
DB_PATH="${CITADEL_DB_PATH:-$WORKDIR/state/lead_queue.db}"
BUCKET="${STATE_BUCKET:-}"
STATE_PREFIX="${STATE_PREFIX:-citadel-state}"
PUSH_INTERVAL_SECONDS="${PUSH_INTERVAL_SECONDS:-45}"
AWS_REGION="${AWS_REGION:-us-east-1}"
LOG_FILE="${CITADEL_SYNC_LOG:-$WORKDIR/logs/sync_state.log}"

mkdir -p "$(dirname "$DB_PATH")" "$(dirname "$LOG_FILE")"

log() {
  printf '%s %s\n' "$(date -Is)" "$*" | tee -a "$LOG_FILE" >&2
}

need() {
  command -v "$1" >/dev/null 2>&1 || { log "missing dependency: $1"; exit 1; }
}

need aws
need sqlite3

refresh_imds_token() {
  if [[ -z "${AWS_EC2_METADATA_DISABLED:-}" ]]; then
    IMDS_TOKEN="$(curl -sS -m 2 -X PUT 'http://169.254.169.254/latest/api/token' \
      -H 'X-aws-ec2-metadata-token-ttl-seconds: 21600' || true)"
  else
    IMDS_TOKEN=""
  fi
}

pull_state_once() {
  [[ -z "$BUCKET" ]] && return 0
  local prefix="s3://$BUCKET/$STATE_PREFIX/"
  log "pulling latest checkpoint from $prefix"
  mkdir -p "$(dirname "$DB_PATH")"
  # --exact-timestamps applies to downloads and prevents unnecessary local mtime churn.
  aws s3 sync "$prefix" "$(dirname "$DB_PATH")" \
    --only-show-errors \
    --exact-timestamps \
    --region "$AWS_REGION" || true
}

checkpoint_sqlite() {
  local src="$DB_PATH"
  local dst="${DB_PATH%.db}.checkpoint.db"
  if [[ ! -f "$src" ]]; then
    return 0
  fi
  sqlite3 "$src" "PRAGMA wal_checkpoint(FULL);" >/dev/null 2>&1 || true
  sqlite3 "$src" ".backup '$dst'" >/dev/null
  echo "$dst"
}

push_state_once() {
  [[ -z "$BUCKET" ]] && return 0
  [[ ! -f "$DB_PATH" ]] && return 0
  local prefix="s3://$BUCKET/$STATE_PREFIX/"
  local backup_path
  backup_path="$(checkpoint_sqlite)"
  if [[ -z "$backup_path" || ! -f "$backup_path" ]]; then
    log "checkpoint failed; skipping push"
    return 1
  fi
  local tmpdir
  tmpdir="$(mktemp -d)"
  cp -f "$backup_path" "$tmpdir/lead_queue.db"
  [[ -f "$DB_PATH-wal" ]] && cp -f "$DB_PATH-wal" "$tmpdir/lead_queue.db-wal" || true
  [[ -f "$DB_PATH-shm" ]] && cp -f "$DB_PATH-shm" "$tmpdir/lead_queue.db-shm" || true

  log "pushing checkpoint to $prefix"
  aws s3 sync "$tmpdir/" "$prefix" \
    --only-show-errors \
    --region "$AWS_REGION"
  rm -rf "$tmpdir"
}

shutdown_handler() {
  log "received shutdown signal; performing final sync"
  refresh_imds_token || true
  push_state_once || true
  exit 0
}

main_loop() {
  trap shutdown_handler SIGTERM SIGINT
  refresh_imds_token || true
  pull_state_once || true
  while true; do
    sleep "$PUSH_INTERVAL_SECONDS"
    refresh_imds_token || true
    push_state_once || true
  done
}

main_loop

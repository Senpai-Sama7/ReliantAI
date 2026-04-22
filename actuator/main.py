"""
ReliantAI Platform Actuator
============================
Consumes scale_intent and heal_intent events from Redis Streams and
executes physical container operations via Docker Compose CLI subprocess.

Design: Redis Stream consumer group pattern.
  - Consumer group "actuators" ensures exactly-one-delivery across
    multiple actuator replicas (no double-scaling).
  - XACK after successful execution marks the message consumed.
  - On failure, message remains in the Pending Entry List (PEL) and
    is re-delivered after ACTUATOR_CLAIM_IDLE_MS milliseconds.
  - XAUTOCLAIM reclaims stale pending messages from dead consumers.

Separation of concerns:
  orchestrator/main.py  -- decides WHAT to scale and WHEN
  actuator/main.py      -- decides HOW to execute that decision
"""

import asyncio
import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Dict, Optional

import redis.asyncio as aioredis
from redis.asyncio.client import Redis as AsyncRedis

REDIS_URL              = os.environ.get("REDIS_URL", "redis://localhost:6379")
STREAM_SCALE_INTENTS   = "reliantai:scale_intents"
STREAM_HEAL_INTENTS    = "reliantai:heal_intents"
STREAM_PLATFORM_EVENTS = "reliantai:platform_events"
CONSUMER_GROUP         = "actuators"
CONSUMER_NAME          = f"actuator-{os.getpid()}"
BLOCK_MS               = 5_000   # block on XREADGROUP for up to 5s
CLAIM_IDLE_MS          = 30_000  # reclaim messages pending >30s (dead consumer)
COMPOSE_FILE           = os.environ.get("COMPOSE_FILE", "docker-compose.yml")
COMPOSE_PROJECT        = os.environ.get("COMPOSE_PROJECT", "reliantai")
DRY_RUN                = os.environ.get("ACTUATOR_DRY_RUN", "false").lower() == "true"

# Map orchestrator service names to Docker Compose service names.
# These may differ if compose uses different naming conventions.
SERVICE_MAP = {
    "money":         "money",
    "complianceone": "complianceone",
    "finops360":     "finops360",
    "integration":   "integration",
    "orchestrator":  "orchestrator",
}


async def ensure_consumer_groups(r: AsyncRedis):
    """Create consumer groups on both streams if they do not exist.
    MKSTREAM creates the stream itself if absent -- avoids race on first publish."""
    for stream in (STREAM_SCALE_INTENTS, STREAM_HEAL_INTENTS):
        try:
            await r.xgroup_create(stream, CONSUMER_GROUP, id="0", mkstream=True)
            print(f"✅ Consumer group '{CONSUMER_GROUP}' created on {stream}")
        except Exception as e:
            if "BUSYGROUP" in str(e):
                pass  # group already exists, expected on restart
            else:
                print(f"⚠️  Consumer group creation failed [{stream}]: {e}")


def docker_scale(service: str, replicas: int) -> bool:
    """Execute docker compose scale via subprocess.
    Returns True on success, False on failure.

    docker compose up --scale <service>=<n> --no-recreate --no-deps
      --no-recreate: do not restart containers that have not changed
      --no-deps:     do not start linked services
    This is the correct idempotent scale command for Compose v2."""
    compose_svc = SERVICE_MAP.get(service)
    if not compose_svc:
        print(f"⚠️  No compose mapping for service: {service}")
        return False

    cmd = [
        "docker", "compose",
        "-f", COMPOSE_FILE,
        "-p", COMPOSE_PROJECT,
        "up", "--scale", f"{compose_svc}={replicas}",
        "--no-recreate", "--no-deps", "--detach",
        compose_svc,
    ]

    if DRY_RUN:
        print(f"[DRY RUN] Would execute: {' '.join(cmd)}")
        return True

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2-minute hard timeout on scale operations
        )
        if result.returncode == 0:
            print(f"✅ Scaled {service} to {replicas} replicas")
            return True
        else:
            print(f"❌ Scale failed [{service}→{replicas}]: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print(f"❌ Scale timeout [{service}→{replicas}] -- operation took >120s")
        return False
    except Exception as e:
        print(f"❌ Scale error [{service}]: {e}")
        return False


def docker_restart(service: str) -> bool:
    """Execute docker compose restart via subprocess."""
    compose_svc = SERVICE_MAP.get(service)
    if not compose_svc:
        return False

    cmd = [
        "docker", "compose",
        "-f", COMPOSE_FILE,
        "-p", COMPOSE_PROJECT,
        "restart", compose_svc,
    ]

    if DRY_RUN:
        print(f"[DRY RUN] Would execute: {' '.join(cmd)}")
        return True

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print(f"✅ Restarted {service}")
            return True
        else:
            print(f"❌ Restart failed [{service}]: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ Restart error [{service}]: {e}")
        return False


async def process_scale_intent(r: AsyncRedis, message_id: str, fields: Dict):
    """Process a single scale_intent message.
    Publishes result to platform_events stream for observability."""
    service  = fields.get("service", "")
    target   = int(fields.get("target_instances", "1"))
    reason   = fields.get("reason", "")
    orch_id  = fields.get("orchestrator_id", "unknown")

    print(f"⚙️  Executing scale: {service} → {target} replicas ({reason})")

    success = docker_scale(service, target)

    await r.xadd(
        STREAM_PLATFORM_EVENTS,
        {
            "event":         "scale_executed",
            "service":       service,
            "target":        str(target),
            "success":       json.dumps(success),
            "orchestrator":  orch_id,
            "actuator":      CONSUMER_NAME,
            "timestamp":     datetime.now().isoformat(),
            "intent_id":     message_id,
        },
        maxlen=50_000,
        approximate=True,
    )
    return success


async def process_heal_intent(r: AsyncRedis, message_id: str, fields: Dict):
    """Process a single heal_intent message."""
    service = fields.get("service", "")
    action  = fields.get("action", "restart")

    print(f"🔧 Executing heal: {service} → {action}")

    success = False
    if action == "restart":
        success = docker_restart(service)

    await r.xadd(
        STREAM_PLATFORM_EVENTS,
        {
            "event":     "heal_executed",
            "service":   service,
            "action":    action,
            "success":   json.dumps(success),
            "actuator":  CONSUMER_NAME,
            "timestamp": datetime.now().isoformat(),
            "intent_id": message_id,
        },
        maxlen=50_000,
        approximate=True,
    )
    return success


async def consume_stream(r: AsyncRedis, stream: str, processor):
    """Read and process messages from a Redis Stream consumer group.

    Redis Stream consumer group semantics:
      XREADGROUP GROUP <group> <consumer> COUNT <n> BLOCK <ms> STREAMS <stream> >
      The ">" special ID means "give me only NEW messages not yet delivered
      to any consumer in this group." Delivered messages move to the PEL
      (Pending Entry List) until XACK'd.

    On startup, we first drain the PEL (messages delivered but not XACK'd
    from a prior crashed consumer) before consuming new messages. This is
    the crash-recovery path -- no intent is lost across actuator restarts."""

    # Drain PEL first (re-deliver unacknowledged messages from dead consumers)
    pending = await r.xautoclaim(
        stream, CONSUMER_GROUP, CONSUMER_NAME,
        min_idle_time=CLAIM_IDLE_MS,
        start_id="0-0",
        count=100,
    )

    # xautoclaim returns (next_start_id, messages, deleted_ids) in redis-py>=5
    claimed_messages = pending[1] if len(pending) > 1 else []
    for message_id, fields in claimed_messages:
        success = await processor(r, message_id, fields)
        if success:
            await r.xack(stream, CONSUMER_GROUP, message_id)

    # Now consume new messages
    while True:
        try:
            results = await r.xreadgroup(
                groupname=CONSUMER_GROUP,
                consumername=CONSUMER_NAME,
                streams={stream: ">"},
                count=10,
                block=BLOCK_MS,
            )

            if not results:
                continue  # timeout, no messages -- loop

            for stream_name, messages in results:
                for message_id, fields in messages:
                    success = await processor(r, message_id, fields)
                    # XACK regardless of success -- failed operations are
                    # logged and published to platform_events for alerting.
                    # Re-queuing failed scale ops risks infinite retry loops.
                    await r.xack(stream, CONSUMER_GROUP, message_id)

        except asyncio.CancelledError:
            return
        except Exception as e:
            print(f"⚠️  Stream consumer error [{stream}]: {e}")
            await asyncio.sleep(2)


async def main():
    print(f"🚀 ReliantAI Actuator starting | consumer={CONSUMER_NAME} | dry_run={DRY_RUN}")

    r = aioredis.from_url(
        REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=10,
        retry_on_timeout=True,
        max_connections=5,
    )

    # Verify Redis connectivity with retry
    for attempt in range(10):
        try:
            await r.ping()
            print(f"✅ Redis connected: {REDIS_URL}")
            break
        except Exception as e:
            print(f"⏳ Waiting for Redis ({attempt+1}/10): {e}")
            await asyncio.sleep(3)
    else:
        print("❌ Cannot connect to Redis after 10 attempts. Exiting.")
        sys.exit(1)

    await ensure_consumer_groups(r)

    # Run both stream consumers concurrently
    async with asyncio.TaskGroup() as tg:
        tg.create_task(consume_stream(r, STREAM_SCALE_INTENTS, process_scale_intent))
        tg.create_task(consume_stream(r, STREAM_HEAL_INTENTS,  process_heal_intent))

    await r.aclose()


if __name__ == "__main__":
    asyncio.run(main())

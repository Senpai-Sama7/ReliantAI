# ADR-003: Use Redis Streams over Kafka for Orchestrator Internal Communication

## Status
Accepted (2024-02-15)

## Context
The orchestrator produces scale/heal intents that downstream consumers (actuator,
dashboard WebSockets, audit log) must process. Requirements:

1. **At-least-once delivery**: Scale-up intent must never be lost.
2. **Ordered processing**: Scale intents for the same service must be processed
   in publication order (serialization).
3. **Low latency**: < 100ms from publish to consumer read.
4. **Operational simplicity**: Single infra component, minimal moving parts.

## Decision
Use **Redis Streams** (`XADD`/`XREAD`) on the shared Redis instance for orchestrator
internal communication, while Kafka is reserved for APEX agent event bus (external
integration channel).

### Streams
```python
# Orchestrator publishes
await redis.xadd("reliantai:scale_intents", {
    "service": "money",
    "target_instances": 5,
    "reason": "cpu_predicted_85",
    "timestamp": time.time()
})

# Actuator consumes
messages = await redis.xread({"reliantai:scale_intents": "$"}, count=1, block=5000)
```

## Consequences

### Positive
- **Single operational surface** — Redis already used for sessions, rate limiting,
  token revocation. No new Kafka cluster to operate.
- **Sub-millisecond latency** — streams live in memory; no disk I/O for hot data.
- **Built-in consumer groups** — `XREADGROUP` provides exactly-once semantics
  with automatic failover if a consumer dies.
- **Persistence** — AOF + RDB means stream data survives restarts (configurable).
- **Simpler topology** — No ZooKeeper, no partition rebalancing, no schema registry.

### Negative
- **Not a distributed log** — Redis is single-node (or Sentinel/Cluster). A Redis
  failure pauses all stream processing until failover completes.
- **Memory-bound** — Old stream entries must be explicitly trimmed (`XTRIM` or `MAXLEN`)
  or memory grows unbounded.
- **No cross-datacenter replication** — Kafka MirrorMaker handles this natively;
  Redis requires custom replication.
- **Limited ecosystem** — No Kafka Connect, no ksqlDB, no Debezium CDC.

## Mitigation
- Memory cap: `XADD ... MAXLEN ~ 10000` to auto-trim old entries.
- HA: Redis Sentinel provides automatic failover (< 30s).
- Persistence: AOF everysec + RDB every 5min.
- Separate channel: APEX agents use Kafka (port 9092) for cross-system events;
  orchestrator streams use Redis (port 6379) for internal platform signals.

## Alternatives Considered
- **Kafka for everything**: Rejected — operational overhead of 3-node Kafka cluster
  for a single stream of scale intents is unjustified. Kafka is used for APEX agent
  events (higher volume, external consumers).
- **PostgreSQL LISTEN/NOTIFY**: Rejected — no persistence of missed notifications;
  consumer disconnect = data loss.
- **RabbitMQ**: Rejected — adds another message broker to operate; Redis already
  serves 4 other use cases (cache, sessions, rate limiting, token revocation).
- **NATS JetStream**: Rejected — promising but unfamiliar to ops team; Redis is
  already in the skill set.

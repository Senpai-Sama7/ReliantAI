"""
Knowledge Consolidation Service - Extract Reusable Patterns

Identifies successful patterns from system operations and creates reusable
assets: materialized views for frequent queries, composite endpoints for
common API sequences, skill shortcuts for effective agent tool combinations.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import json
import hashlib
from collections import defaultdict

import asyncpg


class PatternType(Enum):
    """Types of patterns that can be consolidated."""
    QUERY_PATTERN = "query_pattern"          # Frequent database queries
    API_SEQUENCE = "api_sequence"          # Common API call patterns
    TOOL_COMBINATION = "tool_combination"  # Effective agent tool usage
    PARAMETER_SET = "parameter_set"        # Optimal parameter configurations
    DECISION_PATH = "decision_path"        # Successful decision sequences


class ConsolidationStatus(Enum):
    """Status of pattern consolidation."""
    IDENTIFIED = "identified"              # Pattern detected but not validated
    VALIDATING = "validating"              # Undergoing A/B validation
    CONSOLIDATED = "consolidated"          # Successfully extracted and deployed
    REJECTED = "rejected"                  # Failed validation
    DEPRECATED = "deprecated"              # No longer relevant


@dataclass
class PatternSignature:
    """Signature for identifying patterns."""
    signature_hash: str
    context_features: Dict[str, Any]
    frequency: int
    first_seen: datetime
    last_seen: datetime
    
    def compute_hash(self, features: Dict[str, Any]) -> str:
        """Compute deterministic hash from features."""
        canonical = json.dumps(features, sort_keys=True)
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]


@dataclass
class ConsolidatedKnowledge:
    """A piece of extracted and deployed knowledge."""
    knowledge_id: str
    pattern_type: PatternType
    status: ConsolidationStatus
    
    # Source pattern details
    signature: PatternSignature
    supporting_evidence_count: int
    confidence_score: float
    
    # The consolidated artifact
    artifact_type: str  # "materialized_view", "composite_endpoint", "skill_shortcut"
    artifact_definition: Dict[str, Any]
    
    # Deployment
    deployment_location: Optional[str] = None
    usage_count: int = 0
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    validated_at: Optional[datetime] = None
    last_used: Optional[datetime] = None


@dataclass
class QueryPattern:
    """Pattern for frequent database queries."""
    query_template: str
    parameter_keys: List[str]
    avg_execution_time_ms: float
    result_schema: Dict[str, str]
    cache_hit_rate: float
    
    def should_materialize(self) -> bool:
        """Check if query should become materialized view."""
        # Materialize if: expensive, frequent, stable results
        return (
            self.avg_execution_time_ms > 100 and
            self.cache_hit_rate > 0.7
        )


@dataclass
class APISequencePattern:
    """Pattern for common API call sequences."""
    sequence: List[str]  # ["GET /users/{id}", "GET /users/{id}/orders", ...]
    avg_total_latency_ms: float
    correlation_key: Optional[str]  # Parameter that links calls
    
    def should_create_composite(self) -> bool:
        """Check if should create composite endpoint."""
        return len(self.sequence) >= 2 and self.avg_total_latency_ms > 500


@dataclass
class ToolCombinationPattern:
    """Pattern for effective agent tool usage."""
    tools_used: List[str]
    context_type: str
    success_rate: float
    avg_completion_time_ms: float
    
    def should_create_skill(self) -> bool:
        """Check if should create skill shortcut."""
        return self.success_rate > 0.8 and len(self.tools_used) >= 2


class KnowledgeConsolidator:
    """
    Extracts reusable patterns from system telemetry and creates
    consolidated knowledge assets.
    
    Process:
    1. IDENTIFY: Detect frequent patterns from telemetry
    2. VALIDATE: A/B test against baseline
    3. CONSOLIDATE: Deploy as materialized view, endpoint, or skill
    4. MONITOR: Track usage and performance
    """
    
    def __init__(self, db_pool: Optional[asyncpg.Pool] = None):
        self.db_pool = db_pool
        
        # Pattern detection
        self.query_patterns: Dict[str, QueryPattern] = {}
        self.api_sequences: Dict[str, APISequencePattern] = {}
        self.tool_combinations: Dict[str, ToolCombinationPattern] = {}
        
        # Consolidated knowledge
        self.knowledge_base: Dict[str, ConsolidatedKnowledge] = {}
        
        # Detection state
        self._recent_queries: List[Dict[str, Any]] = []
        self._recent_api_calls: List[Dict[str, Any]] = []
        self._recent_tool_usage: List[Dict[str, Any]] = []
        self._max_buffer_size = 10000
        
        # Processing
        self._is_running = False
        self._consolidation_task: Optional[asyncio.Task] = None
        
        # Thresholds
        self.min_frequency = 10  # Minimum occurrences to consider
        self.min_confidence = 0.7
        self.validation_period_hours = 24
    
    async def initialize(self):
        """Initialize database and load existing knowledge."""
        if not self.db_pool:
            self.db_pool = await asyncpg.create_pool(
                "postgresql://localhost:5435/metacognitive"
            )
        
        await self._ensure_schema()
        await self._load_existing_knowledge()
        
        print("✅ Knowledge Consolidator initialized")
    
    async def _ensure_schema(self):
        """Create knowledge consolidation tables."""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS consolidated_knowledge (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    knowledge_id VARCHAR(128) UNIQUE,
                    pattern_type VARCHAR(64),
                    status VARCHAR(32),
                    signature_hash VARCHAR(32),
                    context_features JSONB,
                    frequency INTEGER DEFAULT 0,
                    confidence_score FLOAT DEFAULT 0.0,
                    artifact_type VARCHAR(64),
                    artifact_definition JSONB,
                    deployment_location VARCHAR(256),
                    usage_count INTEGER DEFAULT 0,
                    created_at TIMESTAMPTZ DEFAULT NOW(),
                    validated_at TIMESTAMPTZ,
                    last_used TIMESTAMPTZ
                );
                
                CREATE INDEX IF NOT EXISTS idx_knowledge_status 
                    ON consolidated_knowledge(status);
                CREATE INDEX IF NOT EXISTS idx_knowledge_type 
                    ON consolidated_knowledge(pattern_type);
                CREATE INDEX IF NOT EXISTS idx_knowledge_confidence 
                    ON consolidated_knowledge(confidence_score DESC);
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS pattern_telemetry (
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    timestamp TIMESTAMPTZ DEFAULT NOW(),
                    pattern_type VARCHAR(64),
                    signature_hash VARCHAR(32),
                    features JSONB,
                    outcome JSONB,
                    duration_ms INTEGER
                );
                
                CREATE INDEX IF NOT EXISTS idx_telemetry_pattern 
                    ON pattern_telemetry(signature_hash);
                CREATE INDEX IF NOT EXISTS idx_telemetry_time 
                    ON pattern_telemetry(timestamp DESC);
            """)
    
    async def _load_existing_knowledge(self):
        """Load previously consolidated knowledge."""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM consolidated_knowledge 
                WHERE status = 'consolidated'
            """)
            
            for row in rows:
                sig = PatternSignature(
                    signature_hash=row['signature_hash'],
                    context_features=row['context_features'],
                    frequency=row['frequency'],
                    first_seen=row['created_at'],
                    last_seen=row['last_used'] or row['created_at']
                )
                
                knowledge = ConsolidatedKnowledge(
                    knowledge_id=row['knowledge_id'],
                    pattern_type=PatternType(row['pattern_type']),
                    status=ConsolidationStatus(row['status']),
                    signature=sig,
                    supporting_evidence_count=row['frequency'],
                    confidence_score=row['confidence_score'],
                    artifact_type=row['artifact_type'],
                    artifact_definition=row['artifact_definition'],
                    deployment_location=row['deployment_location'],
                    usage_count=row['usage_count'],
                    created_at=row['created_at'],
                    validated_at=row['validated_at'],
                    last_used=row['last_used']
                )
                
                self.knowledge_base[knowledge.knowledge_id] = knowledge
        
        print(f"📚 Loaded {len(self.knowledge_base)} consolidated patterns")
    
    async def record_query(self, query: str, parameters: Dict[str, Any],
                          execution_time_ms: float, result_count: int):
        """Record a database query for pattern analysis."""
        normalized = self._normalize_query(query)
        
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'query_template': normalized,
            'parameters': list(parameters.keys()),
            'execution_time_ms': execution_time_ms,
            'result_count': result_count
        }
        
        self._recent_queries.append(entry)
        
        # Limit buffer size
        if len(self._recent_queries) > self._max_buffer_size:
            self._recent_queries = self._recent_queries[-self._max_buffer_size:]
        
        # Persist
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO pattern_telemetry 
                (pattern_type, signature_hash, features, outcome, duration_ms)
                VALUES ($1, $2, $3, $4, $5)
            """,
                PatternType.QUERY_PATTERN.value,
                self._hash_query(normalized),
                json.dumps(entry),
                json.dumps({'result_count': result_count}),
                int(execution_time_ms)
            )
    
    async def record_api_call(self, method: str, path: str, 
                             parameters: Dict[str, Any],
                             latency_ms: float, correlation_id: Optional[str] = None):
        """Record an API call for sequence analysis."""
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'endpoint': f"{method} {path}",
            'parameters': parameters,
            'latency_ms': latency_ms,
            'correlation_id': correlation_id
        }
        
        self._recent_api_calls.append(entry)
        
        if len(self._recent_api_calls) > self._max_buffer_size:
            self._recent_api_calls = self._recent_api_calls[-self._max_buffer_size:]
    
    async def record_tool_usage(self, tools: List[str], context_type: str,
                               success: bool, duration_ms: float):
        """Record agent tool usage for combination analysis."""
        entry = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'tools': sorted(tools),
            'context_type': context_type,
            'success': success,
            'duration_ms': duration_ms
        }
        
        self._recent_tool_usage.append(entry)
        
        if len(self._recent_tool_usage) > self._max_buffer_size:
            self._recent_tool_usage = self._recent_tool_usage[-self._max_buffer_size:]
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for pattern matching."""
        # Remove literals, standardize spacing
        import re
        # Replace string literals with placeholder
        query = re.sub(r"'[^']*'", "'?'", query)
        # Replace numbers with placeholder
        query = re.sub(r"\b\d+\b", "?", query)
        # Normalize whitespace
        query = ' '.join(query.split())
        return query.lower()
    
    def _hash_query(self, query: str) -> str:
        """Hash a normalized query."""
        return hashlib.sha256(query.encode()).hexdigest()[:16]
    
    async def start_consolidation_loop(self, interval_seconds: float = 3600.0):
        """Start periodic pattern consolidation."""
        self._is_running = True
        
        self._consolidation_task = asyncio.create_task(
            self._consolidation_loop(interval_seconds)
        )
        
        print(f"📦 Knowledge consolidation started (interval: {interval_seconds}s)")
    
    async def _consolidation_loop(self, interval: float):
        """Main consolidation loop."""
        while self._is_running:
            try:
                await self._run_consolidation_cycle()
                await asyncio.sleep(interval)
            except Exception as e:
                print(f"⚠️ Consolidation error: {e}")
                await asyncio.sleep(300)
    
    async def _run_consolidation_cycle(self):
        """Run a single consolidation cycle."""
        print("🔍 Running pattern consolidation...")
        
        # Analyze query patterns
        await self._analyze_query_patterns()
        
        # Analyze API sequences
        await self._analyze_api_sequences()
        
        # Analyze tool combinations
        await self._analyze_tool_combinations()
        
        # Validate pending patterns
        await self._validate_pending_patterns()
        
        # Deploy validated patterns
        await self._deploy_validated_patterns()
    
    async def _analyze_query_patterns(self):
        """Identify frequent query patterns."""
        if len(self._recent_queries) < self.min_frequency:
            return
        
        # Group by template
        template_stats = defaultdict(lambda: {
            'count': 0,
            'times': [],
            'parameters': set()
        })
        
        for entry in self._recent_queries:
            template = entry['query_template']
            stats = template_stats[template]
            stats['count'] += 1
            stats['times'].append(entry['execution_time_ms'])
            stats['parameters'].update(entry['parameters'])
        
        # Identify candidates
        for template, stats in template_stats.items():
            if stats['count'] >= self.min_frequency:
                avg_time = sum(stats['times']) / len(stats['times'])
                
                pattern = QueryPattern(
                    query_template=template,
                    parameter_keys=list(stats['parameters']),
                    avg_execution_time_ms=avg_time,
                    result_schema={},  # Would infer from actual results
                    cache_hit_rate=0.8  # Would calculate from telemetry
                )
                
                if pattern.should_materialize():
                    await self._propose_query_consolidation(pattern, stats['count'])
    
    async def _propose_query_consolidation(self, pattern: QueryPattern, frequency: int):
        """Propose consolidating a query pattern."""
        knowledge_id = f"query_{self._hash_query(pattern.query_template)}"
        
        # Skip if already exists
        if knowledge_id in self.knowledge_base:
            return
        
        sig = PatternSignature(
            signature_hash=self._hash_query(pattern.query_template),
            context_features={'query_template': pattern.query_template},
            frequency=frequency,
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc)
        )
        
        artifact = {
            'view_name': f"mv_{knowledge_id}",
            'query_template': pattern.query_template,
            'refresh_interval': '1 hour',
            'estimated_size_mb': 10
        }
        
        knowledge = ConsolidatedKnowledge(
            knowledge_id=knowledge_id,
            pattern_type=PatternType.QUERY_PATTERN,
            status=ConsolidationStatus.IDENTIFIED,
            signature=sig,
            supporting_evidence_count=frequency,
            confidence_score=min(0.9, 0.5 + frequency / 100),
            artifact_type="materialized_view",
            artifact_definition=artifact
        )
        
        self.knowledge_base[knowledge_id] = knowledge
        await self._persist_knowledge(knowledge)
        
        print(f"📊 Identified query pattern: {knowledge_id} "
              f"({frequency} occurrences, {pattern.avg_execution_time_ms:.0f}ms avg)")
    
    async def _analyze_api_sequences(self):
        """Identify common API call sequences."""
        if len(self._recent_api_calls) < self.min_frequency:
            return
        
        # Group by correlation ID
        correlated_calls = defaultdict(list)
        for entry in self._recent_api_calls:
            if entry.get('correlation_id'):
                correlated_calls[entry['correlation_id']].append(entry)
        
        # Find sequences
        sequence_counts = defaultdict(lambda: {'count': 0, 'latencies': []})
        
        for corr_id, calls in correlated_calls.items():
            if len(calls) >= 2:
                sequence = tuple(c['endpoint'] for c in sorted(calls, key=lambda x: x['timestamp']))
                total_latency = sum(c['latency_ms'] for c in calls)
                sequence_counts[sequence]['count'] += 1
                sequence_counts[sequence]['latencies'].append(total_latency)
        
        # Identify candidates
        for sequence, stats in sequence_counts.items():
            if stats['count'] >= self.min_frequency:
                avg_latency = sum(stats['latencies']) / len(stats['latencies'])
                
                pattern = APISequencePattern(
                    sequence=list(sequence),
                    avg_total_latency_ms=avg_latency,
                    correlation_key='user_id'  # Infer from parameter overlap
                )
                
                if pattern.should_create_composite():
                    await self._propose_sequence_consolidation(pattern, stats['count'])
    
    async def _propose_sequence_consolidation(self, pattern: APISequencePattern, frequency: int):
        """Propose consolidating an API sequence."""
        seq_hash = hashlib.sha256(str(tuple(pattern.sequence)).encode()).hexdigest()[:16]
        knowledge_id = f"api_seq_{seq_hash}"
        
        if knowledge_id in self.knowledge_base:
            return
        
        sig = PatternSignature(
            signature_hash=seq_hash,
            context_features={'sequence': pattern.sequence},
            frequency=frequency,
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc)
        )
        
        artifact = {
            'endpoint_path': f"/composite/{knowledge_id}",
            'methods': pattern.sequence,
            'aggregated_response': True
        }
        
        knowledge = ConsolidatedKnowledge(
            knowledge_id=knowledge_id,
            pattern_type=PatternType.API_SEQUENCE,
            status=ConsolidationStatus.IDENTIFIED,
            signature=sig,
            supporting_evidence_count=frequency,
            confidence_score=min(0.85, 0.5 + frequency / 100),
            artifact_type="composite_endpoint",
            artifact_definition=artifact
        )
        
        self.knowledge_base[knowledge_id] = knowledge
        await self._persist_knowledge(knowledge)
        
        print(f"🔗 Identified API sequence: {knowledge_id} "
              f"({len(pattern.sequence)} calls, {frequency} occurrences)")
    
    async def _analyze_tool_combinations(self):
        """Identify effective tool combinations."""
        if len(self._recent_tool_usage) < self.min_frequency:
            return
        
        # Group by context and tool set
        combo_stats = defaultdict(lambda: {
            'count': 0,
            'successes': 0,
            'times': []
        })
        
        for entry in self._recent_tool_usage:
            key = (entry['context_type'], tuple(entry['tools']))
            stats = combo_stats[key]
            stats['count'] += 1
            if entry['success']:
                stats['successes'] += 1
            stats['times'].append(entry['duration_ms'])
        
        # Identify candidates
        for (context, tools), stats in combo_stats.items():
            if stats['count'] >= self.min_frequency:
                success_rate = stats['successes'] / stats['count']
                avg_time = sum(stats['times']) / len(stats['times'])
                
                pattern = ToolCombinationPattern(
                    tools_used=list(tools),
                    context_type=context,
                    success_rate=success_rate,
                    avg_completion_time_ms=avg_time
                )
                
                if pattern.should_create_skill():
                    await self._propose_tool_consolidation(pattern, stats['count'])
    
    async def _propose_tool_consolidation(self, pattern: ToolCombinationPattern, frequency: int):
        """Propose consolidating a tool combination."""
        tools_hash = hashlib.sha256(str(tuple(pattern.tools_used)).encode()).hexdigest()[:16]
        knowledge_id = f"tool_combo_{tools_hash}"
        
        if knowledge_id in self.knowledge_base:
            return
        
        sig = PatternSignature(
            signature_hash=tools_hash,
            context_features={
                'tools': pattern.tools_used,
                'context_type': pattern.context_type
            },
            frequency=frequency,
            first_seen=datetime.now(timezone.utc),
            last_seen=datetime.now(timezone.utc)
        )
        
        artifact = {
            'skill_name': f"combo_{pattern.context_type}",
            'tools': pattern.tools_used,
            'preconditions': {'context_type': pattern.context_type}
        }
        
        knowledge = ConsolidatedKnowledge(
            knowledge_id=knowledge_id,
            pattern_type=PatternType.TOOL_COMBINATION,
            status=ConsolidationStatus.IDENTIFIED,
            signature=sig,
            supporting_evidence_count=frequency,
            confidence_score=pattern.success_rate,
            artifact_type="skill_shortcut",
            artifact_definition=artifact
        )
        
        self.knowledge_base[knowledge_id] = knowledge
        await self._persist_knowledge(knowledge)
        
        print(f"🛠️ Identified tool combination: {knowledge_id} "
              f"({len(pattern.tools_used)} tools, {pattern.success_rate:.0%} success)")
    
    async def _validate_pending_patterns(self):
        """Validate patterns that have been identified."""
        now = datetime.now(timezone.utc)
        
        for knowledge in self.knowledge_base.values():
            if knowledge.status != ConsolidationStatus.IDENTIFIED:
                continue
            
            # Check if validation period elapsed
            elapsed = (now - knowledge.created_at).total_seconds() / 3600
            if elapsed < self.validation_period_hours:
                continue
            
            # Validate by checking if pattern is still occurring
            recent_count = await self._count_recent_occurrences(knowledge.signature.signature_hash)
            
            if recent_count >= self.min_frequency // 2:  # At least half frequency
                knowledge.status = ConsolidationStatus.VALIDATING
                knowledge.validated_at = now
                await self._persist_knowledge(knowledge)
                print(f"✅ Pattern {knowledge.knowledge_id} validated")
            else:
                knowledge.status = ConsolidationStatus.REJECTED
                await self._persist_knowledge(knowledge)
                print(f"❌ Pattern {knowledge.knowledge_id} rejected (frequency dropped)")
    
    async def _count_recent_occurrences(self, signature_hash: str) -> int:
        """Count recent occurrences of a pattern."""
        async with self.db_pool.acquire() as conn:
            row = await conn.fetchval("""
                SELECT COUNT(*) FROM pattern_telemetry
                WHERE signature_hash = $1
                AND timestamp > NOW() - INTERVAL '24 hours'
            """, signature_hash)
            return row or 0
    
    async def _deploy_validated_patterns(self):
        """Deploy validated patterns as knowledge assets."""
        for knowledge in self.knowledge_base.values():
            if knowledge.status != ConsolidationStatus.VALIDATING:
                continue
            
            # Deploy based on artifact type
            success = await self._deploy_artifact(knowledge)
            
            if success:
                knowledge.status = ConsolidationStatus.CONSOLIDATED
                knowledge.deployment_location = self._get_deployment_location(knowledge)
                await self._persist_knowledge(knowledge)
                print(f"🚀 Deployed {knowledge.artifact_type}: {knowledge.knowledge_id}")
    
    async def _deploy_artifact(self, knowledge: ConsolidatedKnowledge) -> bool:
        """Deploy a knowledge artifact."""
        artifact = knowledge.artifact_definition
        
        try:
            if knowledge.artifact_type == "materialized_view":
                # Would create actual materialized view
                print(f"   Would create materialized view: {artifact.get('view_name')}")
                return True
                
            elif knowledge.artifact_type == "composite_endpoint":
                # Would register composite endpoint
                print(f"   Would register endpoint: {artifact.get('endpoint_path')}")
                return True
                
            elif knowledge.artifact_type == "skill_shortcut":
                # Would register skill shortcut
                print(f"   Would register skill: {artifact.get('skill_name')}")
                return True
                
        except Exception as e:
            print(f"   Deployment failed: {e}")
            return False
        
        return False
    
    def _get_deployment_location(self, knowledge: ConsolidatedKnowledge) -> Optional[str]:
        """Get deployment location for an artifact."""
        artifact = knowledge.artifact_definition
        
        if knowledge.artifact_type == "materialized_view":
            return f"database.views.{artifact.get('view_name')}"
        elif knowledge.artifact_type == "composite_endpoint":
            return f"api.composite.{artifact.get('endpoint_path')}"
        elif knowledge.artifact_type == "skill_shortcut":
            return f"apex.skills.{artifact.get('skill_name')}"
        
        return None
    
    async def _persist_knowledge(self, knowledge: ConsolidatedKnowledge):
        """Persist knowledge to database."""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO consolidated_knowledge 
                (knowledge_id, pattern_type, status, signature_hash, 
                 context_features, frequency, confidence_score,
                 artifact_type, artifact_definition, deployment_location,
                 usage_count, validated_at, last_used)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (knowledge_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    frequency = EXCLUDED.frequency,
                    confidence_score = EXCLUDED.confidence_score,
                    deployment_location = EXCLUDED.deployment_location,
                    usage_count = EXCLUDED.usage_count,
                    validated_at = EXCLUDED.validated_at,
                    last_used = EXCLUDED.last_used
            """,
                knowledge.knowledge_id,
                knowledge.pattern_type.value,
                knowledge.status.value,
                knowledge.signature.signature_hash,
                json.dumps(knowledge.signature.context_features),
                knowledge.supporting_evidence_count,
                knowledge.confidence_score,
                knowledge.artifact_type,
                json.dumps(knowledge.artifact_definition),
                knowledge.deployment_location,
                knowledge.usage_count,
                knowledge.validated_at,
                knowledge.last_used
            )
    
    async def record_artifact_usage(self, knowledge_id: str):
        """Record that a consolidated artifact was used."""
        if knowledge_id in self.knowledge_base:
            knowledge = self.knowledge_base[knowledge_id]
            knowledge.usage_count += 1
            knowledge.last_used = datetime.now(timezone.utc)
            await self._persist_knowledge(knowledge)
    
    def get_consolidation_stats(self) -> Dict[str, Any]:
        """Get knowledge consolidation statistics."""
        by_status = {}
        by_type = {}
        
        for knowledge in self.knowledge_base.values():
            status = knowledge.status.value
            by_status[status] = by_status.get(status, 0) + 1
            
            ptype = knowledge.pattern_type.value
            by_type[ptype] = by_type.get(ptype, 0) + 1
        
        consolidated = [k for k in self.knowledge_base.values() 
                       if k.status == ConsolidationStatus.CONSOLIDATED]
        
        total_usage = sum(k.usage_count for k in consolidated)
        
        return {
            'total_patterns': len(self.knowledge_base),
            'by_status': by_status,
            'by_type': by_type,
            'consolidated_patterns': len(consolidated),
            'total_artifact_usage': total_usage,
            'avg_confidence': sum(k.confidence_score for k in self.knowledge_base.values()) / len(self.knowledge_base) if self.knowledge_base else 0,
            'telemetry_buffer': {
                'queries': len(self._recent_queries),
                'api_calls': len(self._recent_api_calls),
                'tool_usage': len(self._recent_tool_usage)
            }
        }
    
    def get_applicable_knowledge(self, context: Dict[str, Any]) -> List[ConsolidatedKnowledge]:
        """Get knowledge applicable to current context."""
        applicable = []
        
        for knowledge in self.knowledge_base.values():
            if knowledge.status != ConsolidationStatus.CONSOLIDATED:
                continue
            
            # Check if context matches
            features = knowledge.signature.context_features
            match_score = 0
            total = 0
            
            for key, value in features.items():
                if key in context:
                    total += 1
                    if context[key] == value:
                        match_score += 1
            
            if total > 0 and match_score / total > 0.8:
                applicable.append(knowledge)
        
        # Sort by confidence
        applicable.sort(key=lambda k: k.confidence_score, reverse=True)
        return applicable[:5]
    
    def stop(self):
        """Stop consolidation loop."""
        self._is_running = False
        if self._consolidation_task:
            self._consolidation_task.cancel()
        print("🛑 Knowledge Consolidator stopped")


# Singleton accessor
_consolidator: Optional[KnowledgeConsolidator] = None


async def get_consolidator() -> KnowledgeConsolidator:
    """Get or create singleton consolidator."""
    global _consolidator
    if _consolidator is None:
        _consolidator = KnowledgeConsolidator()
        await _consolidator.initialize()
    return _consolidator

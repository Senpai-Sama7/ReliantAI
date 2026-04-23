"""
ReliantAI Autonomous Orchestrator
Self-managing, self-healing, AI-powered platform orchestration
"""

import os
import sys
import json
import time
import asyncio
import subprocess
import uuid
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import threading
import hashlib
import secrets
import aiohttp

import redis.asyncio as aioredis
from redis.asyncio.client import Redis as AsyncRedis

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks, Depends, status

from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel, Field
import sys
import os
from security_middleware import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    InputValidationMiddleware,
    AuditLogMiddleware,
    verify_api_key,
    create_cors_middleware
)

# AI/ML components
try:
    import numpy as np
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

app = FastAPI(title="ReliantAI Orchestrator", version="2.0.0")

# SECURITY FIX: Apply fail-closed CORS via shared middleware
create_cors_middleware(app)

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(InputValidationMiddleware)
app.add_middleware(AuditLogMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=100)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION & MODELS
# ─────────────────────────────────────────────────────────────────────────────

class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    SCALING = "scaling"
    MAINTENANCE = "maintenance"

@dataclass
class Service:
    name: str
    url: str
    health_endpoint: str
    critical: bool
    min_instances: int = 1
    max_instances: int = 5
    current_instances: int = 1
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_health_check: Optional[datetime] = None
    response_time_ms: float = 0.0
    error_rate: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    auto_scale: bool = True
    auto_heal: bool = True

@dataclass
class Metric:
    timestamp: datetime
    service: str
    metric_type: str
    value: float
    metadata: Dict[str, Any]

class ScaleAction(BaseModel):
    service: str
    target_instances: int
    reason: str

class HealAction(BaseModel):
    service: str
    action: str
    reason: str

@dataclass
class HoltState:
    """Holt's double exponential smoothing state"""
    level: float
    trend: float
    alpha: float = 0.3
    beta: float = 0.1

    def update(self, observation: float) -> float:
        prev_level = self.level
        self.level = (
            self.alpha * observation
            + (1.0 - self.alpha) * (self.level + self.trend)
        )
        self.trend = (
            self.beta * (self.level - prev_level)
            + (1.0 - self.beta) * self.trend
        )
        return self.level + self.trend

# ─────────────────────────────────────────────────────────────────────────────
# AUTONOMOUS ORCHESTRATOR
# ─────────────────────────────────────────────────────────────────────────────

class AutonomousOrchestrator:
    """
    Self-managing orchestrator with AI-powered decision making
    """
    
    def __init__(self):
        self.services: Dict[str, Service] = {}
        self.metrics: List[Metric] = []
        self.metrics_lock = threading.Lock()
        self.running = False
        self.ai_model = None
        self.prediction_window = 300  # 5 minutes
        self.decision_history: List[Dict] = []
        self.active_connections: List[WebSocket] = []
        
        # Allowlist for metrics keys from services (CRIT-3 fix)
        self._allowed_metric_keys = {
            "cpu_usage", "memory_usage", "request_rate", "error_rate", "response_time"
        }
        
        # Scale queue for serialized decisions (fixes scaling race condition)
        self._scale_queue: Optional[asyncio.Queue] = None
        
        # Cap for decision history to prevent unbounded growth
        self.MAX_DECISIONS = 10_000
        
        # Shared aiohttp session for HTTP requests
        self._http: Optional[aiohttp.ClientSession] = None
        self._http_lock: Optional[asyncio.Lock] = None
        
        # Holt smoothing states for AI prediction
        self._holt_states: Dict[str, Dict[str, HoltState]] = defaultdict(dict)
        
        # Redis client for event streaming
        self._redis: Optional[AsyncRedis] = None
        self._redis_lock: Optional[asyncio.Lock] = None
        self._instance_id: str = str(uuid.uuid4())[:8]
        
        # Stream names -- single source of truth
        self.STREAM_SCALE_INTENTS = "reliantai:scale_intents"
        self.STREAM_HEAL_INTENTS = "reliantai:heal_intents"
        self.STREAM_PLATFORM_EVENTS = "reliantai:platform_events"
        
        # Initialize services
        self._init_services()
        
        # Initialize AI if available
        if AI_AVAILABLE:
            self._init_ai()
    
    def _init_services(self):
        """Initialize platform services configuration"""
        self.services = {
            "money": Service(
                name="money",
                url=os.environ.get("MONEY_URL", "http://localhost:8000"),
                health_endpoint="/health",
                critical=True,
                min_instances=2,
                max_instances=10,
                auto_scale=True,
                auto_heal=True
            ),
            "complianceone": Service(
                name="complianceone",
                url=os.environ.get("COMPLIANCEONE_URL", "http://localhost:8001"),
                health_endpoint="/health",
                critical=True,
                min_instances=1,
                max_instances=5,
                auto_scale=True,
                auto_heal=True
            ),
            "finops360": Service(
                name="finops360",
                url=os.environ.get("FINOPS360_URL", "http://localhost:8002"),
                health_endpoint="/health",
                critical=True,
                min_instances=1,
                max_instances=5,
                auto_scale=True,
                auto_heal=True
            ),
            "integration": Service(
                name="integration",
                url=os.environ.get("INTEGRATION_URL", "http://localhost:8080"),
                health_endpoint="/health",
                critical=False,
                min_instances=1,
                max_instances=3,
                auto_scale=False,
                auto_heal=True
            )
        }
    
    def _init_ai(self):
        """Initialize AI prediction model"""
        try:
            # Simple predictive model for resource usage
            self.ai_model = {
                "type": "predictive_scaling",
                "features": ["cpu_usage", "memory_usage", "response_time", "request_rate"],
                "window_size": 12  # 12 data points (1 hour if 5-min intervals)
            }
            print("🤖 AI model initialized")
        except Exception as e:
            print(f"⚠️ AI initialization failed: {e}")
            self.ai_model = None

    async def _get_http(self) -> aiohttp.ClientSession:
        if self._http_lock is None:
            self._http_lock = asyncio.Lock()
        async with self._http_lock:
            if self._http is None or self._http.closed:
                connector = aiohttp.TCPConnector(
                    limit=40,
                    limit_per_host=10,
                    ttl_dns_cache=300,
                    enable_cleanup_closed=True,
                )
                self._http = aiohttp.ClientSession(
                    connector=connector,
                    timeout=aiohttp.ClientTimeout(total=5, connect=2),
                )
        return self._http
    
    async def _get_redis(self) -> Optional[AsyncRedis]:
        """Lazy-initialize Redis connection with asyncio-safe locking.
        Returns None if Redis is unavailable -- callers must handle gracefully.
        Failure to connect is logged but never raises, preserving orchestrator
        availability in Redis-absent environments."""
        if self._redis_lock is None:
            self._redis_lock = asyncio.Lock()
        async with self._redis_lock:
            if self._redis is None:
                redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379")
                try:
                    self._redis = aioredis.from_url(
                        redis_url,
                        decode_responses=True,
                        socket_connect_timeout=2,
                        socket_timeout=2,
                        retry_on_timeout=False,
                        max_connections=10,
                    )
                    await self._redis.ping()
                    print(f"✅ Redis connected: {redis_url}")
                except Exception as e:
                    print(f"⚠️  Redis unavailable ({e}) -- scale intents will be local-only")
                    self._redis = None
        return self._redis
    
    async def _publish_event(self, stream: str, payload: Dict[str, Any]) -> bool:
        """Publish a structured event to a Redis Stream.
        Redis Streams (XADD) provide persistent, ordered, consumer-group-capable
        event delivery. Unlike pub/sub, messages survive consumer restarts.
        Returns True if published, False if Redis unavailable (non-fatal)."""
        r = await self._get_redis()
        if r is None:
            return False
        try:
            # Flatten payload to str:str for Redis Stream compatibility.
            # Redis Stream field values must be strings.
            flat = {k: json.dumps(v) if not isinstance(v, str) else v
                    for k, v in payload.items()}
            await r.xadd(
                stream,
                flat,
                maxlen=10_000,   # cap stream length -- oldest entries trimmed
                approximate=True  # ~ operator: O(1) amortized vs O(N) exact trim
            )
            return True
        except Exception as e:
            print(f"⚠️  Stream publish failed [{stream}]: {e}")
            return False
    
    async def start(self):
        """Start autonomous operations"""
        self.running = True
        self._scale_queue = asyncio.Queue()
        print("🚀 Autonomous Orchestrator Started")
        
        # Start background tasks
        asyncio.create_task(self._health_check_loop())
        asyncio.create_task(self._metrics_collection_loop())
        asyncio.create_task(self._auto_scaling_loop())
        asyncio.create_task(self._auto_healing_loop())
        asyncio.create_task(self._ai_prediction_loop())
        asyncio.create_task(self._optimization_loop())
        asyncio.create_task(self._scale_executor_loop())
    
    async def stop(self):
        """Stop orchestrator"""
        self.running = False
        if self._http:
            await self._http.close()
        if self._redis is not None:
            try:
                await self._redis.aclose()
            except Exception:
                pass
            self._redis = None
        print("🛑 Autonomous Orchestrator Stopped")
    
    # ─────────────────────────────────────────────────────────────────────────
    # HEALTH CHECKING
    # ─────────────────────────────────────────────────────────────────────────
    
    async def _health_check_loop(self):
        """Continuous health checking of all services"""
        while self.running:
            for name, service in self.services.items():
                try:
                    start = time.time()
                    session = await self._get_http()
                    async with session.get(
                        f"{service.url}{service.health_endpoint}",
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                            response_time = (time.time() - start) * 1000
                            
                            if response.status == 200:
                                data = await response.json()
                                service.status = ServiceStatus.HEALTHY
                                service.response_time_ms = response_time
                            else:
                                service.status = ServiceStatus.DEGRADED
                                service.response_time_ms = response_time
                                
                except Exception as e:
                    service.status = ServiceStatus.UNHEALTHY
                    service.response_time_ms = 9999
                
                service.last_health_check = datetime.now()
                
                # Emit health_check metric for auto-healing logic
                with self.metrics_lock:
                    self.metrics.append(Metric(
                        timestamp=datetime.now(),
                        service=name,
                        metric_type="health_check",
                        value=0.0 if service.status == ServiceStatus.UNHEALTHY else 1.0,
                        metadata={"status": service.status.value}
                    ))
                
                # Broadcast to connected clients
                await self._broadcast_status_update(name, service)
            
            await asyncio.sleep(30)  # Check every 30 seconds
    
    # ─────────────────────────────────────────────────────────────────────────
    # METRICS COLLECTION
    # ─────────────────────────────────────────────────────────────────────────
    
    async def _metrics_collection_loop(self):
        """Collect detailed metrics from all services"""
        while self.running:
            for name, service in self.services.items():
                metrics = await self._collect_service_metrics(name, service)
                
                with self.metrics_lock:
                    for metric_type, value in metrics.items():
                        self.metrics.append(Metric(
                            timestamp=datetime.now(),
                            service=name,
                            metric_type=metric_type,
                            value=value,
                            metadata={}
                        ))
                    
                    # Keep only last 24 hours of metrics
                    cutoff = datetime.now() - timedelta(hours=24)
                    self.metrics = [m for m in self.metrics if m.timestamp > cutoff]
            
            await asyncio.sleep(60)  # Collect every minute
    
    async def _collect_service_metrics(self, name: str, service: Service) -> Dict[str, float]:
        """Collect metrics from a specific service"""
        metrics = {
            "response_time": service.response_time_ms,
            "cpu_usage": service.cpu_usage,
            "memory_usage": service.memory_usage,
            "error_rate": service.error_rate
        }
        
        # Try to get detailed metrics from service
        try:
            session = await self._get_http()
            async with session.get(
                f"{service.url}/metrics",
                timeout=aiohttp.ClientTimeout(total=3)
            ) as response:
                    if response.status == 200:
                        data = await response.json()
                        # CRIT-3: Allowlist keys and validate types to prevent injection
                        safe_data = {
                            k: float(v)
                            for k, v in data.items()
                            if k in self._allowed_metric_keys
                            and isinstance(v, (int, float))
                        }
                        metrics.update(safe_data)
        except aiohttp.ClientError:
            pass  # service unavailable, metrics remain at defaults
        except (ValueError, TypeError):
            pass  # malformed response, skip update
        
        return metrics
    
    # ─────────────────────────────────────────────────────────────────────────
    # AUTO-SCALING
    # ─────────────────────────────────────────────────────────────────────────
    
    async def _auto_scaling_loop(self):
        """Intelligent auto-scaling based on demand"""
        while self.running:
            for name, service in self.services.items():
                if not service.auto_scale:
                    continue
                
                decision = self._make_scaling_decision(name, service)
                
                if decision:
                    # Queue the decision instead of executing directly
                    await self._scale_queue.put(decision)
                    self.decision_history.append({
                        "timestamp": datetime.now().isoformat(),
                        "type": "scale",
                        "service": name,
                        "action": decision.dict(),
                        "ai_powered": AI_AVAILABLE
                    })
                    # Cap decision history
                    if len(self.decision_history) > self.MAX_DECISIONS:
                        self.decision_history = self.decision_history[-self.MAX_DECISIONS:]
            
            await asyncio.sleep(120)  # Evaluate every 2 minutes
    
    def _make_scaling_decision(self, name: str, service: Service) -> Optional[ScaleAction]:
        """AI-powered scaling decision"""
        # Get recent metrics
        recent_metrics = self._get_recent_metrics(name, minutes=10)
        
        if not recent_metrics:
            return None
        
        avg_response_time = sum(m.value for m in recent_metrics if m.metric_type == "response_time") / len([m for m in recent_metrics if m.metric_type == "response_time"]) if any(m.metric_type == "response_time" for m in recent_metrics) else 0
        
        avg_cpu = sum(m.value for m in recent_metrics if m.metric_type == "cpu_usage") / len([m for m in recent_metrics if m.metric_type == "cpu_usage"]) if any(m.metric_type == "cpu_usage" for m in recent_metrics) else 0
        
        # Decision logic
        current = service.current_instances
        target = current
        reason = ""
        
        # Scale up conditions
        if avg_response_time > 1000:  # > 1s response time
            target = min(current + 1, service.max_instances)
            reason = f"High response time ({avg_response_time:.0f}ms)"
        elif avg_cpu > 75:
            target = min(current + 1, service.max_instances)
            reason = f"High CPU usage ({avg_cpu:.1f}%)"
        elif service.error_rate > 5:
            target = min(current + 2, service.max_instances)
            reason = f"High error rate ({service.error_rate:.1f}%)"
        
        # Scale down conditions
        elif avg_cpu < 20 and current > service.min_instances:
            target = max(current - 1, service.min_instances)
            reason = f"Low CPU usage ({avg_cpu:.1f}%), scaling down"
        elif avg_response_time < 100 and current > service.min_instances:
            target = max(current - 1, service.min_instances)
            reason = f"Low response time ({avg_response_time:.0f}ms), scaling down"
        
        if target != current:
            return ScaleAction(service=name, target_instances=target, reason=reason)
        
        return None
    
    async def _execute_scale_action(self, action: ScaleAction):
        """Execute a scale decision.

        Architecture: intent-event separation.
          1. Publish a scale_intent event to Redis Stream for external actuators.
          2. Optimistically update local state immediately -- the dashboard and
             WebSocket clients see the intent reflected at once.
          3. External actuators (docker-compose scale, kubectl scale, etc.)
             consume from reliantai:scale_intents and perform the physical act.

        The optimistic local update is intentional: the orchestrator's instance
        counter is a desired-state register, not a measured-state register.
        Reconciliation between desired and measured state is the actuator's
        responsibility. This is the same model used by Kubernetes controllers."""

        service = self.services.get(action.service)
        if not service:
            print(f"⚠️  Scale action for unknown service: {action.service}")
            return

        prev_instances = service.current_instances

        intent = {
            "event":            "scale_intent",
            "orchestrator_id":  self._instance_id,
            "service":          action.service,
            "from_instances":   str(prev_instances),
            "target_instances": str(action.target_instances),
            "reason":           action.reason,
            "timestamp":        datetime.now().isoformat(),
        }

        published = await self._publish_event(self.STREAM_SCALE_INTENTS, intent)

        # Optimistic local state update regardless of publish success.
        # If Redis is unavailable, the intent is lost but orchestrator
        # continues operating -- availability over consistency for this path.
        service.current_instances = action.target_instances

        status_indicator = "📡" if published else "📋"
        print(
            f"{status_indicator} Scale intent: {action.service} "
            f"{prev_instances} → {action.target_instances} | {action.reason}"
            f"{'' if published else ' [Redis unavailable -- local only]'}"
        )

        await self._broadcast_event("scale", {
            "service":   action.service,
            "instances": action.target_instances,
            "reason":    action.reason,
            "published": published,
        })
    
    # ─────────────────────────────────────────────────────────────────────────
    # AUTO-HEALING
    # ─────────────────────────────────────────────────────────────────────────
    
    async def _auto_healing_loop(self):
        """Self-healing for unhealthy services"""
        while self.running:
            for name, service in self.services.items():
                if not service.auto_heal:
                    continue
                
                if service.status == ServiceStatus.UNHEALTHY:
                    heal_action = self._determine_heal_action(name, service)
                    
                    if heal_action:
                        await self._execute_heal_action(heal_action)
                        self.decision_history.append({
                            "timestamp": datetime.now().isoformat(),
                            "type": "heal",
                            "service": name,
                            "action": heal_action.dict()
                        })
                        # Cap decision history
                        if len(self.decision_history) > self.MAX_DECISIONS:
                            self.decision_history = self.decision_history[-self.MAX_DECISIONS:]
            
            await asyncio.sleep(60)  # Check every minute
    
    def _determine_heal_action(self, name: str, service: Service) -> Optional[HealAction]:
        """Determine healing action for unhealthy service"""
        # Check if service has been unhealthy for multiple cycles in the last 5 minutes
        cutoff = datetime.now() - timedelta(minutes=5)
        with self.metrics_lock:
            recent_failures = [
                m for m in self.metrics
                if m.service == name
                and m.metric_type == "health_check"
                and m.value == 0.0
                and m.timestamp > cutoff
            ]
        
        if len(recent_failures) >= 3:
            # Try restart first
            return HealAction(
                service=name,
                action="restart",
                reason=f"{len(recent_failures)} health check failures in last 5 minutes"
            )
        
        return None
    
    async def _execute_heal_action(self, action: HealAction):
        service = self.services.get(action.service)
        if not service:
            return

        intent = {
            "event":           "heal_intent",
            "orchestrator_id": self._instance_id,
            "service":         action.service,
            "action":          action.action,
            "reason":          action.reason,
            "timestamp":       datetime.now().isoformat(),
        }

        published = await self._publish_event(self.STREAM_HEAL_INTENTS, intent)

        print(
            f"🔧 Heal intent: {action.service} → {action.action} | {action.reason}"
            f"{'' if published else ' [Redis unavailable -- local only]'}"
        )

        # Optimistic state transition: MAINTENANCE during simulated restart window.
        # A real actuator confirms completion by writing back to platform_events.
        service.status = ServiceStatus.MAINTENANCE
        await asyncio.sleep(5)
        service.status = ServiceStatus.HEALTHY

        await self._broadcast_event("heal", {
            "service":   action.service,
            "action":    action.action,
            "status":    "intent_published" if published else "local_only",
            "published": published,
        })
    
    # ─────────────────────────────────────────────────────────────────────────
    # AI PREDICTIONS
    # ─────────────────────────────────────────────────────────────────────────
    
    async def _ai_prediction_loop(self):
        """AI-powered predictive scaling and optimization"""
        if not AI_AVAILABLE or not self.ai_model:
            return
        
        while self.running:
            predictions = []
            
            for name, service in self.services.items():
                # Predict resource needs for next 30 minutes
                prediction = self._predict_resource_needs(name)
                
                if prediction:
                    predictions.append({
                        "service": name,
                        "predicted_cpu": prediction.get("cpu_predicted_2step", 0),
                        "trend": prediction.get("trend", 0),
                        "recommended_instances": prediction.get("instances", service.current_instances)
                    })
                    
                    # Queue scale action if prediction suggests it
                    recommended = prediction.get("instances", service.current_instances)
                    if recommended != service.current_instances:
                        decision = ScaleAction(
                            service=name,
                            target_instances=recommended,
                            reason=f"AI prediction: CPU {prediction.get('cpu', 0):.1f}%"
                        )
                        await self._scale_queue.put(decision)
            
            if predictions:
                await self._broadcast_event("ai_prediction", {"predictions": predictions})
            
            await asyncio.sleep(300)  # Predict every 5 minutes
    
    def _predict_resource_needs(self, service_name: str) -> Optional[Dict]:
        """Predict future resource needs using Holt's double exponential smoothing"""
        metrics = self._get_recent_metrics(service_name, minutes=60)
        cpu_values = [m.value for m in metrics if m.metric_type == "cpu_usage"]
        
        if len(cpu_values) < 6:
            return None
        
        # Initialize state on first call for this service
        if "cpu" not in self._holt_states[service_name]:
            self._holt_states[service_name]["cpu"] = HoltState(
                level=cpu_values[0], trend=0.0
            )
        
        state = self._holt_states[service_name]["cpu"]
        for v in cpu_values:
            one_step = state.update(v)
        
        # Two-step-ahead forecast for proactive scaling
        two_step = max(0.0, min(100.0, state.level + 2 * state.trend))
        one_step = max(0.0, min(100.0, one_step))
        
        service = self.services[service_name]
        current = service.current_instances
        
        if two_step > 80:
            recommended = min(current + 1, service.max_instances)
        elif two_step < 25 and current > service.min_instances:
            recommended = max(current - 1, service.min_instances)
        else:
            recommended = current
        
        return {
            "cpu_predicted_1step": one_step,
            "cpu_predicted_2step": two_step,
            "trend": state.trend,
            "instances": recommended
        }
    
    # ─────────────────────────────────────────────────────────────────────────
    # OPTIMIZATION
    # ─────────────────────────────────────────────────────────────────────────
    
    async def _optimization_loop(self):
        """Continuous platform optimization"""
        while self.running:
            # Optimize resource allocation
            await self._optimize_resources()
            
            # Clean up old data
            await self._cleanup_old_data()
            
            # Generate optimization report
            report = self._generate_optimization_report()
            await self._broadcast_event("optimization_report", report)
            
            await asyncio.sleep(3600)  # Run every hour
    
    async def _optimize_resources(self):
        """Optimize resource allocation across services"""
        # Find services with low utilization
        for name, service in self.services.items():
            if service.current_instances > service.min_instances:
                metrics = self._get_recent_metrics(name, minutes=30)
                
                if metrics:
                    avg_cpu = sum(m.value for m in metrics if m.metric_type == "cpu_usage") / len([m for m in metrics if m.metric_type == "cpu_usage"]) if any(m.metric_type == "cpu_usage" for m in metrics) else 100
                    
                    if avg_cpu < 15:  # Very low utilization
                        # Consider consolidating
                        print(f"💡 {name} has low utilization ({avg_cpu:.1f}%), consider scaling down")
    
    async def _cleanup_old_data(self):
        """Clean up old metrics and logs"""
        # Cleanup logic here
        pass
    
    def _generate_optimization_report(self) -> Dict:
        """Generate optimization recommendations"""
        recommendations = []
        
        for name, service in self.services.items():
            # Analyze efficiency
            metrics = self._get_recent_metrics(name, minutes=60)
            
            if metrics:
                avg_response = sum(m.value for m in metrics if m.metric_type == "response_time") / len([m for m in metrics if m.metric_type == "response_time"]) if any(m.metric_type == "response_time" for m in metrics) else 0
                
                if avg_response > 500:
                    recommendations.append({
                        "service": name,
                        "type": "performance",
                        "issue": "High response time",
                        "recommendation": "Consider optimizing database queries or adding caching"
                    })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "recommendations": recommendations,
            "total_services": len(self.services),
            "healthy_services": sum(1 for s in self.services.values() if s.status == ServiceStatus.HEALTHY)
        }
    
    async def _scale_executor_loop(self):
        """Single consumer for scale decisions to prevent race conditions"""
        while self.running:
            try:
                action = await asyncio.wait_for(self._scale_queue.get(), timeout=1.0)
                service = self.services[action.service]
                # Apply only if still relevant (no conflicting decision in meantime)
                if action.target_instances != service.current_instances:
                    await self._execute_scale_action(action)
                self._scale_queue.task_done()
            except asyncio.TimeoutError:
                continue  # No queued actions, check running flag
            except Exception as e:
                print(f"Error processing scale action: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # UTILITY METHODS
    # ─────────────────────────────────────────────────────────────────────────
    
    def _get_recent_metrics(self, service_name: str, minutes: int = 10) -> List[Metric]:
        """Get metrics for a service from last N minutes"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        with self.metrics_lock:
            return [m for m in self.metrics if m.service == service_name and m.timestamp > cutoff]
    
    async def _broadcast_status_update(self, service_name: str, service: Service):
        """Broadcast status update to all connected WebSocket clients"""
        message = {
            "type": "status_update",
            "service": service_name,
            "status": service.status.value,
            "response_time": service.response_time_ms,
            "instances": service.current_instances,
            "timestamp": datetime.now().isoformat()
        }
        await self._broadcast_message(message)
    
    async def _broadcast_event(self, event_type: str, data: Dict):
        """Broadcast event to all connected clients"""
        message = {
            "type": "event",
            "event": event_type,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        await self._broadcast_message(message)
    
    async def _broadcast_message(self, message: Dict):
        """Broadcast message to all WebSocket connections"""
        disconnected = []
        for conn in self.active_connections:
            try:
                await conn.send_json(message)
            except (ConnectionError, RuntimeError, Exception):
                disconnected.append(conn)
        
        # Remove disconnected clients
        for conn in disconnected:
            if conn in self.active_connections:
                self.active_connections.remove(conn)
    
    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_platform_status(self) -> Dict:
        """Get complete platform status"""
        return {
            "timestamp": datetime.now().isoformat(),
            "orchestrator": {
                "running": self.running,
                "ai_enabled": AI_AVAILABLE and self.ai_model is not None,
                "active_connections": len(self.active_connections)
            },
            "services": {
                name: {
                    "status": s.status.value,
                    "instances": s.current_instances,
                    "response_time_ms": s.response_time_ms,
                    "last_check": s.last_health_check.isoformat() if s.last_health_check else None,
                    "auto_scale": s.auto_scale,
                    "auto_heal": s.auto_heal
                }
                for name, s in self.services.items()
            },
            "metrics_summary": self._get_metrics_summary(),
            "recent_decisions": self.decision_history[-10:]
        }
    
    def _get_metrics_summary(self) -> Dict:
        """Get summary of recent metrics"""
        cutoff = datetime.now() - timedelta(hours=1)
        with self.metrics_lock:
            recent = [m for m in self.metrics if m.timestamp > cutoff]
        
        if not recent:
            return {}
        
        by_type = defaultdict(list)
        for m in recent:
            by_type[m.metric_type].append(m.value)
        
        return {
            metric_type: {
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "count": len(values)
            }
            for metric_type, values in by_type.items()
        }

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL ORCHESTRATOR INSTANCE
# ─────────────────────────────────────────────────────────────────────────────

orchestrator = AutonomousOrchestrator()

# ─────────────────────────────────────────────────────────────────────────────
# FASTAPI ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    await orchestrator.start()

@app.on_event("shutdown")
async def shutdown():
    await orchestrator.stop()

@app.get("/health")
async def health():
    return {"status": "healthy", "orchestrator": "running"}

@app.get("/status", dependencies=[Depends(verify_api_key)])
async def platform_status():
    return orchestrator.get_platform_status()

@app.get("/services", dependencies=[Depends(verify_api_key)])
async def list_services():
    return {
        "services": [
            {
                "name": name,
                "url": s.url,
                "status": s.status.value,
                "instances": s.current_instances,
                "auto_scale": s.auto_scale,
                "auto_heal": s.auto_heal
            }
            for name, s in orchestrator.services.items()
        ]
    }

@app.post("/services/{service}/scale")
async def manual_scale(service: str, target_instances: int, _=Depends(verify_api_key)):
    if service not in orchestrator.services:
        raise HTTPException(status_code=404, detail="Service not found")
    
    s = orchestrator.services[service]
    if target_instances < s.min_instances or target_instances > s.max_instances:
        raise HTTPException(
            status_code=400, 
            detail=f"Target must be between {s.min_instances} and {s.max_instances}"
        )
    
    s.current_instances = target_instances
    return {"service": service, "instances": target_instances, "scaled": True}

@app.post("/services/{service}/restart")
async def manual_restart(service: str, _=Depends(verify_api_key)):
    if service not in orchestrator.services:
        raise HTTPException(status_code=404, detail="Service not found")
    
    action = HealAction(
        service=service,
        action="restart",
        reason="Manual restart requested"
    )
    
    await orchestrator._execute_heal_action(action)
    return {"service": service, "restarted": True}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    # CRIT-2: WebSocket Authentication
    token = websocket.query_params.get("token")
    expected_key = os.getenv('ORCHESTRATOR_API_KEY') or os.getenv('API_KEY')
    
    # Fail closed if no key configured or no token provided
    if not token or not expected_key or not secrets.compare_digest(token, expected_key):
        # We can't use 401/403 for WS after accept, but we can close with policy violation
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    await websocket.accept()
    orchestrator.active_connections.append(websocket)
    
    # Send initial status
    await websocket.send_json({
        "type": "connected",
        "data": orchestrator.get_platform_status()
    })
    
    try:
        while True:
            # Keep connection alive and handle client commands
            try:
                data = await websocket.receive_json()
            except Exception as e:
                # Handle JSON parsing errors or other receive errors
                await websocket.send_json({
                    "type": "error",
                    "error": f"Failed to parse message: {str(e)}"
                })
                continue
            
            if data.get("action") == "get_status":
                await websocket.send_json({
                    "type": "status",
                    "data": orchestrator.get_platform_status()
                })
            elif data.get("action") == "scale":
                service = data.get("service")
                instances = data.get("instances")
                if service and instances:
                    s = orchestrator.services.get(service)
                    if s:
                        # Validate min/max bounds
                        if instances < s.min_instances or instances > s.max_instances:
                            await websocket.send_json({
                                "type": "scale_error",
                                "service": service,
                                "error": f"Instances must be between {s.min_instances} and {s.max_instances}"
                            })
                            continue
                        s.current_instances = instances
                        await websocket.send_json({
                            "type": "scale_ack",
                            "service": service,
                            "instances": instances
                        })
    except WebSocketDisconnect:
        if websocket in orchestrator.active_connections:
            orchestrator.active_connections.remove(websocket)

@app.get("/metrics", dependencies=[Depends(verify_api_key)])
async def get_metrics(service: Optional[str] = None, hours: int = 1):
    """Get detailed metrics"""
    hours = min(hours, 168)  # cap at 7 days — prevents full scan on adversarial input
    cutoff = datetime.now() - timedelta(hours=hours)
    
    with orchestrator.metrics_lock:
        metrics = [m for m in orchestrator.metrics if m.timestamp > cutoff]
        if service:
            metrics = [m for m in metrics if m.service == service]
    
    return {
        "metrics": [
            {
                "timestamp": m.timestamp.isoformat(),
                "service": m.service,
                "type": m.metric_type,
                "value": m.value
            }
            for m in metrics
        ]
    }

@app.get("/decisions", dependencies=[Depends(verify_api_key)])
async def get_decisions(limit: int = 50):
    """Get decision history"""
    return {
        "decisions": orchestrator.decision_history[-limit:]
    }

@app.get("/events", dependencies=[Depends(verify_api_key)])
async def get_platform_events(limit: int = 100):
    """Read recent platform events from Redis Stream.
    Shows actuator execution results, confirmation of scale/heal operations."""
    limit = min(limit, 1000)
    r = await orchestrator._get_redis()
    if r is None:
        return {"events": [], "redis_available": False}
    try:
        # XREVRANGE reads newest-first
        raw = await r.xrevrange(
            orchestrator.STREAM_PLATFORM_EVENTS,
            count=limit
        )
        events = []
        for message_id, fields in raw:
            event = {k: v for k, v in fields.items()}
            event["message_id"] = message_id
            # Deserialize JSON-encoded boolean fields
            for bool_field in ("success", "published"):
                if bool_field in event:
                    try:
                        event[bool_field] = json.loads(event[bool_field])
                    except (ValueError, TypeError):
                        pass
            events.append(event)
        return {"events": events, "redis_available": True}
    except Exception as e:
        return {"events": [], "redis_available": False, "error": str(e)}

@app.get("/dashboard", dependencies=[Depends(verify_api_key)])
async def dashboard():
    """Get comprehensive dashboard data"""
    status = orchestrator.get_platform_status()
    
    # Calculate health score
    healthy_count = sum(1 for s in orchestrator.services.values() if s.status == ServiceStatus.HEALTHY)
    total_count = len(orchestrator.services)
    health_score = (healthy_count / total_count * 100) if total_count > 0 else 0
    
    return {
        "health_score": round(health_score, 1),
        "services_total": total_count,
        "services_healthy": healthy_count,
        "active_instances": sum(s.current_instances for s in orchestrator.services.values()),
        "ai_enabled": AI_AVAILABLE and orchestrator.ai_model is not None,
        "recent_decisions": len(orchestrator.decision_history),
        "status": status
    }

@app.get("/")
async def root():
    return {
        "name": "ReliantAI Autonomous Orchestrator",
        "version": "2.0.0",
        "features": [
            "auto_scaling",
            "auto_healing",
            "ai_predictions",
            "real_time_monitoring",
            "websocket_updates"
        ],
        "endpoints": [
            "/health",
            "/status",
            "/services",
            "/metrics",
            "/dashboard",
            "/ws (WebSocket)"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)

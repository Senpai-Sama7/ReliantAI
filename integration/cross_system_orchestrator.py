#!/usr/bin/env python3
"""
ReliantAI Cross-System Orchestrator

Coordinates tasks across all 4 major systems:
- APEX: 4-layer probabilistic agent workflow (L1→L2→L3→L4)
- Money: 5-agent CrewAI HVAC dispatch
- Citadel: NL agent with tool routing
- Acropolis: Rust-based polyglot orchestrator

Provides unified interface for:
1. System discovery and health monitoring
2. Cross-system task delegation
3. Multi-system workflow orchestration
4. Unified observability
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import aiohttp
from pydantic import BaseModel, Field

# Import A2A bridge
from a2a_bridge import (
    A2ABridge, AgentCard, AgentCapability, AgentSkill,
)


# ─────────────────────────────────────────────────────────────────────────────
# System Definitions
# ─────────────────────────────────────────────────────────────────────────────

class SystemType(str, Enum):
    """ReliantAI system types."""
    APEX = "apex"
    MONEY = "money"
    CITADEL = "citadel"
    ACROPOLIS = "acropolis"
    INTEGRATION = "integration"


@dataclass
class SystemEndpoint:
    """Endpoint configuration for a system."""
    name: str
    url: str
    health_path: str = "/health"
    api_version: str = "v1"
    auth_required: bool = True


@dataclass
class SystemInfo:
    """Runtime information about a system."""
    system_type: SystemType
    name: str
    version: str
    status: str  # "healthy", "degraded", "unhealthy", "unknown"
    endpoints: List[SystemEndpoint]
    capabilities: List[str]
    last_health_check: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# Orchestrator Configuration
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class OrchestratorConfig:
    """Configuration for the cross-system orchestrator."""
    # System URLs
    apex_url: str = os.getenv("APEX_AGENTS_URL", "http://localhost:8001")
    money_url: str = os.getenv("MONEY_API_URL", "http://localhost:8000")
    citadel_url: str = os.getenv("CITADEL_URL", "http://localhost:8002")
    acropolis_url: str = os.getenv("ACROPOLIS_URL", "http://localhost:8003")
    integration_url: str = os.getenv("INTEGRATION_URL", "http://localhost:8080")
    event_bus_url: str = os.getenv("EVENT_BUS_URL", "http://localhost:8081")
    mcp_url: str = os.getenv("APEX_MCP_URL", "http://localhost:4000")
    mcp_api_key: str = os.getenv("APEX_MCP_API_KEY", "")
    
    # Operational settings
    health_check_interval: int = 30
    max_concurrent_workflows: int = 50
    default_timeout: int = 300
    enable_auto_recovery: bool = True
    
    # Circuit breaker settings
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 60


# ─────────────────────────────────────────────────────────────────────────────
# Workflow Models
# ─────────────────────────────────────────────────────────────────────────────

class WorkflowStep(BaseModel):
    """A single step in a multi-system workflow."""
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    system: SystemType
    operation: str  # e.g., "apex.workflow.run", "money.sms.dispatch"
    parameters: Dict[str, Any] = Field(default_factory=dict)
    depends_on: List[str] = Field(default_factory=list)
    timeout_seconds: int = 300
    retry_count: int = 3
    condition: Optional[str] = None  # Conditional execution


class WorkflowDefinition(BaseModel):
    """Definition of a cross-system workflow."""
    workflow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    steps: List[WorkflowStep]
    on_failure: str = "abort"  # "abort", "continue", "retry"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowExecution(BaseModel):
    """Runtime state of a workflow execution."""
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str
    status: str = "pending"  # "pending", "running", "completed", "failed"
    step_results: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    current_step: Optional[str] = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class OrchestrationResult(BaseModel):
    """Result of an orchestration operation."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    systems_contacted: List[SystemType] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────────────────
# Cross-System Orchestrator
# ─────────────────────────────────────────────────────────────────────────────

class CrossSystemOrchestrator:
    """
    Orchestrates tasks across all ReliantAI systems.
    
    Provides a unified interface for:
    - System discovery and health monitoring
    - Cross-system task delegation
    - Multi-system workflow execution
    - Unified observability and tracing
    """

    def __init__(self, config: Optional[OrchestratorConfig] = None):
        self.config = config or OrchestratorConfig()
        self.a2a_bridge = A2ABridge()
        self.systems: Dict[SystemType, SystemInfo] = {}
        self.active_workflows: Dict[str, WorkflowExecution] = {}
        self._session: Optional[aiohttp.ClientSession] = None
        self._health_check_task: Optional[asyncio.Task] = None
        self._circuit_breakers: Dict[SystemType, Dict[str, Any]] = {}

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.default_timeout)
            )
        return self._session

    async def initialize(self):
        """Initialize the orchestrator and discover systems."""
        # Start health check loop
        self._health_check_task = asyncio.create_task(self._health_check_loop())
        
        # Discover systems
        await self.discover_systems()
        
        # Initialize A2A bridge
        await self._init_a2a_agents()

    async def shutdown(self):
        """Shutdown the orchestrator and cleanup."""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        
        await self.a2a_bridge.close()
        
        if self._session and not self._session.closed:
            await self._session.close()

    # ── System Discovery ──────────────────────────────────────────────────────

    async def discover_systems(self):
        """Discover and register all available systems."""
        systems_to_check = [
            (SystemType.APEX, "APEX Agent System", self.config.apex_url),
            (SystemType.MONEY, "Money HVAC Dispatch", self.config.money_url),
            (SystemType.CITADEL, "Citadel NL Agent", self.config.citadel_url),
            (SystemType.ACROPOLIS, "Acropolis Orchestrator", self.config.acropolis_url),
        ]
        
        for system_type, name, url in systems_to_check:
            health = await self._check_health(url)
            
            self.systems[system_type] = SystemInfo(
                system_type=system_type,
                name=name,
                version=health.get("version", "unknown"),
                status="healthy" if health.get("ok") else "unhealthy",
                endpoints=[SystemEndpoint(name="api", url=url)],
                capabilities=self._get_system_capabilities(system_type),
                metadata=health,
            )

    def _get_system_capabilities(self, system_type: SystemType) -> List[str]:
        """Get capabilities for a system type."""
        capabilities = {
            SystemType.APEX: [
                "4-layer-workflow",
                "mcp-tool-bus",
                "uncertainty-calibration",
                "hitl-gates",
                "skill-execution",
            ],
            SystemType.MONEY: [
                "crewai-5-agent",
                "hvac-dispatch",
                "sms-integration",
                "calendar-scheduling",
            ],
            SystemType.CITADEL: [
                "nl-agent",
                "tool-routing",
                "chat-completion",
                "kg-vectors",
            ],
            SystemType.ACROPOLIS: [
                "rust-orchestrator",
                "plugin-hot-reload",
                "polyglot-agents",
                "memory-system",
            ],
        }
        return capabilities.get(system_type, [])

    async def _check_health(self, url: str) -> Dict[str, Any]:
        """Check health of a system endpoint."""
        try:
            session = await self._get_session()
            async with session.get(f"{url}/health", timeout=5) as response:
                if response.status == 200:
                    return await response.json()
                return {"ok": False, "status": response.status}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    async def _health_check_loop(self):
        """Background task for periodic health checks."""
        while True:
            try:
                await asyncio.sleep(self.config.health_check_interval)
                
                for system_type, info in self.systems.items():
                    for endpoint in info.endpoints:
                        health = await self._check_health(endpoint.url)
                        info.status = "healthy" if health.get("ok") else "unhealthy"
                        info.last_health_check = datetime.now(UTC)
                        info.metadata = health
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Orchestrator] Health check error: {e}")

    def get_system_status(self, system_type: SystemType) -> Optional[SystemInfo]:
        """Get current status of a system."""
        return self.systems.get(system_type)

    def get_all_system_status(self) -> Dict[SystemType, SystemInfo]:
        """Get status of all systems."""
        return self.systems

    # ── A2A Integration ─────────────────────────────────────────────────────

    async def _init_a2a_agents(self):
        """Initialize A2A agents for all systems."""
        # Register APEX agent
        await self.a2a_bridge.register_agent(AgentCard(
            name="APEX-Orchestrator",
            description="4-layer probabilistic agent workflow",
            url=self.config.apex_url,
            version="1.0.0",
            capabilities=[AgentCapability.STREAMING, AgentCapability.STATE_TRANSITIONS],
            skills=[
                AgentSkill(
                    id="apex-workflow",
                    name="Full Workflow",
                    description="Execute L1→L2→L3→L4 agent pipeline",
                    tags=["workflow", "orchestration", "multi-layer"],
                ),
                AgentSkill(
                    id="apex-tools",
                    name="Tool Execution",
                    description="Execute MCP tools via APEX",
                    tags=["tools", "mcp", "browser", "computer", "code"],
                ),
            ],
        ))
        
        # Register Money agent
        await self.a2a_bridge.register_agent(AgentCard(
            name="Money-HVAC-Dispatch",
            description="5-agent CrewAI HVAC dispatch system",
            url=self.config.money_url,
            version="1.0.0",
            capabilities=[AgentCapability.STATE_TRANSITIONS],
            skills=[
                AgentSkill(
                    id="hvac-triage",
                    name="HVAC Emergency Triage",
                    description="Classify HVAC emergencies by urgency (LIFE_SAFETY, EMERGENCY, URGENT, ROUTINE)",
                    tags=["hvac", "emergency", "triage", "dispatch"],
                ),
            ],
        ))
        
        # Register Citadel agent
        await self.a2a_bridge.register_agent(AgentCard(
            name="Citadel-NL-Agent",
            description="Natural language agent with tool routing",
            url=self.config.citadel_url,
            version="1.0.0",
            capabilities=[AgentCapability.STREAMING],
            skills=[
                AgentSkill(
                    id="nl-chat",
                    name="Conversational AI",
                    description="Chat with tool execution capabilities",
                    tags=["chat", "nlp", "conversation"],
                ),
            ],
        ))

    # ── Cross-System Operations ───────────────────────────────────────────────

    async def execute_on_apex(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        use_full_pipeline: bool = True,
    ) -> OrchestrationResult:
        """
        Execute a task on the APEX system.
        
        Args:
            task: Task description
            context: Additional context
            use_full_pipeline: Use L1→L2→L3→L4 or just Layer 3
            
        Returns:
            OrchestrationResult with execution results
        """
        start_time = datetime.now(UTC)
        
        try:
            session = await self._get_session()
            
            if use_full_pipeline:
                endpoint = f"{self.config.apex_url}/workflow/run"
                payload = {
                    "task": task,
                    "context": context or {},
                }
            else:
                endpoint = f"{self.config.apex_url}/agents/layer3/dispatch"
                payload = {
                    "task": task,
                    "context": context or {},
                }
            
            async with session.post(endpoint, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                
                elapsed = (datetime.now(UTC) - start_time).total_seconds() * 1000
                
                return OrchestrationResult(
                    success=True,
                    data=data,
                    execution_time_ms=elapsed,
                    systems_contacted=[SystemType.APEX],
                )
                
        except Exception as e:
            elapsed = (datetime.now(UTC) - start_time).total_seconds() * 1000
            return OrchestrationResult(
                success=False,
                error=str(e),
                execution_time_ms=elapsed,
                systems_contacted=[SystemType.APEX],
            )

    async def execute_on_money(
        self,
        sms_body: str,
        from_phone: str = "+1234567890",
    ) -> OrchestrationResult:
        """Execute an HVAC dispatch on the Money system."""
        start_time = datetime.now(UTC)
        
        try:
            session = await self._get_session()
            
            async with session.post(
                f"{self.config.money_url}/sms",
                data={"Body": sms_body, "From": from_phone},
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                elapsed = (datetime.now(UTC) - start_time).total_seconds() * 1000
                
                return OrchestrationResult(
                    success=True,
                    data=data,
                    execution_time_ms=elapsed,
                    systems_contacted=[SystemType.MONEY],
                )
                
        except Exception as e:
            elapsed = (datetime.now(UTC) - start_time).total_seconds() * 1000
            return OrchestrationResult(
                success=False,
                error=str(e),
                execution_time_ms=elapsed,
                systems_contacted=[SystemType.MONEY],
            )

    async def execute_on_citadel(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
    ) -> OrchestrationResult:
        """Execute a chat completion on the Citadel system."""
        start_time = datetime.now(UTC)
        
        try:
            session = await self._get_session()
            
            payload = {
                "model": model or "gemini-2.0-flash",
                "messages": messages,
            }
            
            async with session.post(
                f"{self.config.citadel_url}/v1/chat/completions",
                json=payload,
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                elapsed = (datetime.now(UTC) - start_time).total_seconds() * 1000
                
                return OrchestrationResult(
                    success=True,
                    data=data,
                    execution_time_ms=elapsed,
                    systems_contacted=[SystemType.CITADEL],
                )
                
        except Exception as e:
            elapsed = (datetime.now(UTC) - start_time).total_seconds() * 1000
            return OrchestrationResult(
                success=False,
                error=str(e),
                execution_time_ms=elapsed,
                systems_contacted=[SystemType.CITADEL],
            )

    async def execute_mcp_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> OrchestrationResult:
        """Execute a tool via the APEX MCP tool bus."""
        start_time = datetime.now(UTC)
        
        try:
            session = await self._get_session()
            
            headers = {"Content-Type": "application/json"}
            if self.config.mcp_api_key:
                headers["X-API-Key"] = self.config.mcp_api_key
            
            async with session.post(
                f"{self.config.mcp_url}/tools/call",
                json={"name": tool_name, "arguments": arguments},
                headers=headers,
            ) as response:
                response.raise_for_status()
                data = await response.json()
                
                elapsed = (datetime.now(UTC) - start_time).total_seconds() * 1000
                
                return OrchestrationResult(
                    success=data.get("success", False),
                    data=data,
                    execution_time_ms=elapsed,
                    systems_contacted=[SystemType.APEX],
                )
                
        except Exception as e:
            elapsed = (datetime.now(UTC) - start_time).total_seconds() * 1000
            return OrchestrationResult(
                success=False,
                error=str(e),
                execution_time_ms=elapsed,
                systems_contacted=[SystemType.APEX],
            )

    # ── Workflow Execution ────────────────────────────────────────────────────

    async def execute_workflow(
        self,
        workflow: WorkflowDefinition,
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> WorkflowExecution:
        """
        Execute a multi-system workflow.
        
        Args:
            workflow: Workflow definition
            initial_context: Initial context for the workflow
            
        Returns:
            WorkflowExecution with results
        """
        execution = WorkflowExecution(workflow_id=workflow.workflow_id)
        self.active_workflows[execution.execution_id] = execution
        
        execution.status = "running"
        context = initial_context or {}
        
        try:
            # Build dependency graph
            completed_steps: Set[str] = set()
            remaining_steps = {step.step_id: step for step in workflow.steps}
            
            while remaining_steps:
                # Find steps that can execute (dependencies met)
                executable = [
                    step for step in remaining_steps.values()
                    if all(dep in completed_steps for dep in step.depends_on)
                ]
                
                if not executable:
                    raise ValueError("Workflow has circular dependencies or stuck steps")
                
                # Execute all ready steps concurrently
                tasks = [self._execute_step(step, context) for step in executable]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for step, result in zip(executable, results):
                    if isinstance(result, Exception):
                        execution.step_results[step.step_id] = {
                            "success": False,
                            "error": str(result),
                        }
                        
                        if workflow.on_failure == "abort":
                            execution.status = "failed"
                            execution.error_message = f"Step {step.name} failed: {result}"
                            execution.completed_at = datetime.now(UTC)
                            return execution
                    else:
                        execution.step_results[step.step_id] = result
                        context.update(result.get("data", {}))
                        completed_steps.add(step.step_id)
                    
                    del remaining_steps[step.step_id]
            
            execution.status = "completed"
            execution.completed_at = datetime.now(UTC)
            
        except Exception as e:
            execution.status = "failed"
            execution.error_message = str(e)
            execution.completed_at = datetime.now(UTC)
        
        return execution

    async def _execute_step(
        self,
        step: WorkflowStep,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a single workflow step."""
        # Route to appropriate system
        if step.system == SystemType.APEX:
            result = await self.execute_on_apex(
                step.parameters.get("task", ""),
                {**context, **step.parameters},
            )
        elif step.system == SystemType.MONEY:
            result = await self.execute_on_money(
                step.parameters.get("sms_body", ""),
                step.parameters.get("from_phone", "+1234567890"),
            )
        elif step.system == SystemType.CITADEL:
            result = await self.execute_on_citadel(
                step.parameters.get("messages", []),
                step.parameters.get("model"),
            )
        else:
            raise ValueError(f"Unsupported system: {step.system}")
        
        return {
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "execution_time_ms": result.execution_time_ms,
        }

    # ── Intelligent Routing ──────────────────────────────────────────────────

    async def route_task(
        self,
        task_description: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> OrchestrationResult:
        """
        Intelligently route a task to the best system.
        
        Uses keyword matching and system capabilities to determine
        the optimal system for a given task.
        """
        task_lower = task_description.lower()
        
        # HVAC-related tasks go to Money
        hvac_keywords = ["hvac", "ac", "air conditioning", "heating", "cooling", "thermostat", "furnace"]
        if any(kw in task_lower for kw in hvac_keywords):
            return await self.execute_on_money(task_description)
        
        # Chat/NL tasks go to Citadel
        chat_keywords = ["chat", "talk", "ask", "question", "explain", "what is", "how to"]
        if any(kw in task_lower for kw in chat_keywords):
            return await self.execute_on_citadel(
                [{"role": "user", "content": task_description}]
            )
        
        # Complex multi-step tasks go to APEX
        complex_keywords = ["workflow", "analyze", "research", "prospect", "proposal", "dispatch"]
        if any(kw in task_lower for kw in complex_keywords):
            return await self.execute_on_apex(task_description, context)
        
        # Default to APEX
        return await self.execute_on_apex(task_description, context)


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI Integration
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import FastAPI, HTTPException


def create_orchestrator_routes(app: FastAPI, orchestrator: CrossSystemOrchestrator) -> None:
    """
    Register orchestrator routes on a FastAPI app.
    
    Usage:
        app = FastAPI()
        orchestrator = CrossSystemOrchestrator()
        await orchestrator.initialize()
        create_orchestrator_routes(app, orchestrator)
    """

    @app.get("/orchestrator/systems")
    async def list_systems():
        """List all systems and their status."""
        systems = orchestrator.get_all_system_status()
        return {
            "systems": [
                {
                    "type": sys.system_type.value,
                    "name": sys.name,
                    "version": sys.version,
                    "status": sys.status,
                    "capabilities": sys.capabilities,
                    "last_check": sys.last_health_check.isoformat(),
                }
                for sys in systems.values()
            ]
        }

    @app.get("/orchestrator/systems/{system_type}")
    async def get_system(system_type: str):
        """Get detailed info about a specific system."""
        try:
            sys_type = SystemType(system_type)
        except ValueError:
            raise HTTPException(400, f"Invalid system type: {system_type}")
        
        info = orchestrator.get_system_status(sys_type)
        if not info:
            raise HTTPException(404, f"System {system_type} not found")
        
        return {
            "type": info.system_type.value,
            "name": info.name,
            "version": info.version,
            "status": info.status,
            "capabilities": info.capabilities,
            "metadata": info.metadata,
        }

    @app.post("/orchestrator/route")
    async def route_task_endpoint(request: Dict[str, Any]):
        """Route a task to the best system."""
        task = request.get("task", "")
        context = request.get("context", {})
        
        if not task:
            raise HTTPException(400, "Task is required")
        
        result = await orchestrator.route_task(task, context)
        return result.model_dump()

    @app.post("/orchestrator/execute/{system_type}")
    async def execute_on_system(system_type: str, request: Dict[str, Any]):
        """Execute directly on a specific system."""
        try:
            sys_type = SystemType(system_type)
        except ValueError:
            raise HTTPException(400, f"Invalid system type: {system_type}")
        
        if sys_type == SystemType.APEX:
            result = await orchestrator.execute_on_apex(
                request.get("task", ""),
                request.get("context", {}),
                request.get("full_pipeline", True),
            )
        elif sys_type == SystemType.MONEY:
            result = await orchestrator.execute_on_money(
                request.get("sms_body", ""),
                request.get("from_phone", "+1234567890"),
            )
        elif sys_type == SystemType.CITADEL:
            result = await orchestrator.execute_on_citadel(
                request.get("messages", []),
                request.get("model"),
            )
        else:
            raise HTTPException(400, f"Execution not supported for {system_type}")
        
        return result.model_dump()

    @app.post("/orchestrator/workflows")
    async def create_workflow(workflow: WorkflowDefinition):
        """Execute a workflow."""
        execution = await orchestrator.execute_workflow(workflow)
        return execution.model_dump()

    @app.get("/orchestrator/workflows/{execution_id}")
    async def get_workflow(execution_id: str):
        """Get workflow execution status."""
        execution = orchestrator.active_workflows.get(execution_id)
        if not execution:
            raise HTTPException(404, f"Workflow execution {execution_id} not found")
        return execution.model_dump()

    @app.post("/orchestrator/mcp/tool")
    async def execute_mcp_tool(request: Dict[str, Any]):
        """Execute an MCP tool."""
        tool_name = request.get("tool")
        arguments = request.get("arguments", {})
        
        if not tool_name:
            raise HTTPException(400, "Tool name is required")
        
        result = await orchestrator.execute_mcp_tool(tool_name, arguments)
        return result.model_dump()


# ─────────────────────────────────────────────────────────────────────────────
# Singleton Instance
# ─────────────────────────────────────────────────────────────────────────────

_orchestrator_instance: Optional[CrossSystemOrchestrator] = None


def get_orchestrator() -> CrossSystemOrchestrator:
    """Get or create the global orchestrator instance."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = CrossSystemOrchestrator()
    return _orchestrator_instance


async def init_orchestrator() -> CrossSystemOrchestrator:
    """Initialize and return the global orchestrator."""
    orchestrator = get_orchestrator()
    await orchestrator.initialize()
    return orchestrator


# ─────────────────────────────────────────────────────────────────────────────
# CLI for testing
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    
    async def main():
        orchestrator = await init_orchestrator()
        
        if len(sys.argv) < 2:
            print("Usage: cross_system_orchestrator.py <command> [args...]")
            print("Commands: status, route, apex, money, citadel, mcp")
            return
        
        cmd = sys.argv[1]
        
        if cmd == "status":
            systems = orchestrator.get_all_system_status()
            for sys_type, info in systems.items():
                print(f"{sys_type.value}: {info.status} ({info.name})")
        
        elif cmd == "route":
            task = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Hello"
            result = await orchestrator.route_task(task)
            print(f"Routed to: {result.systems_contacted}")
            print(f"Success: {result.success}")
            print(f"Time: {result.execution_time_ms:.0f}ms")
        
        elif cmd == "apex":
            task = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Analyze this"
            result = await orchestrator.execute_on_apex(task)
            print(f"APEX result: {result.success}")
            if result.data:
                print(json.dumps(result.data, indent=2)[:500])
        
        elif cmd == "money":
            sms = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "AC is broken"
            result = await orchestrator.execute_on_money(sms)
            print(f"Money result: {result.success}")
            if result.data:
                print(json.dumps(result.data, indent=2)[:500])
        
        elif cmd == "citadel":
            msg = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Hello"
            result = await orchestrator.execute_on_citadel([{"role": "user", "content": msg}])
            print(f"Citadel result: {result.success}")
            if result.data:
                print(json.dumps(result.data, indent=2)[:500])
        
        elif cmd == "mcp":
            tool = sys.argv[2] if len(sys.argv) > 2 else "brave_search"
            result = await orchestrator.execute_mcp_tool(tool, {"query": "test"})
            print(f"MCP result: {result.success}")
            if result.data:
                print(json.dumps(result.data, indent=2)[:500])
        
        await orchestrator.shutdown()
    
    asyncio.run(main())

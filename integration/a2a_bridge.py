#!/usr/bin/env python3
"""
ReliantAI A2A (Agent-to-Agent) Protocol Bridge

Implements Google's A2A protocol for cross-system agent communication.
Enables agents from APEX, Money, Citadel, and Acropolis to communicate.

References:
- https://github.com/google/A2A
- CrewAI A2A implementation
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, AsyncIterator
from contextlib import asynccontextmanager

import aiohttp
from pydantic import BaseModel, Field

# ─────────────────────────────────────────────────────────────────────────────
# A2A Protocol Models
# ─────────────────────────────────────────────────────────────────────────────

class TaskState(str, Enum):
    """Task lifecycle states per A2A spec."""
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input_required"
    COMPLETED = "completed"
    CANCELED = "canceled"
    FAILED = "failed"


class MessageRole(str, Enum):
    """Message roles in A2A conversations."""
    USER = "user"
    AGENT = "agent"


class ArtifactType(str, Enum):
    """Types of artifacts agents can produce."""
    TEXT = "text"
    FILE = "file"
    DATA = "data"
    ERROR = "error"


class A2AMessage(BaseModel):
    """A message in an A2A conversation."""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class A2AArtifact(BaseModel):
    """An artifact produced by an agent."""
    artifact_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: ArtifactType
    name: str
    content: Any
    mime_type: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class A2ATask(BaseModel):
    """An A2A task representing work to be done."""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    state: TaskState = TaskState.SUBMITTED
    message: A2AMessage
    artifacts: List[A2AArtifact] = Field(default_factory=list)
    history: List[A2AMessage] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    agent_card: Optional[Dict[str, Any]] = None


class A2AStatusUpdate(BaseModel):
    """Status update for streaming."""
    task_id: str
    state: TaskState
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ─────────────────────────────────────────────────────────────────────────────
# Agent Card
# ─────────────────────────────────────────────────────────────────────────────

class AgentCapability(str, Enum):
    """Capabilities an agent can advertise."""
    STREAMING = "streaming"
    PUSH_NOTIFICATIONS = "push_notifications"
    STATE_TRANSITIONS = "state_transitions"


class AgentSkill(BaseModel):
    """A skill an agent can perform."""
    id: str
    name: str
    description: str
    tags: List[str] = Field(default_factory=list)
    examples: List[str] = Field(default_factory=list)


class AgentCard(BaseModel):
    """Agent card describing an agent's capabilities."""
    name: str
    description: str
    url: str
    version: str
    capabilities: List[AgentCapability] = Field(default_factory=list)
    skills: List[AgentSkill] = Field(default_factory=list)
    authentication: Optional[Dict[str, Any]] = None
    default_input_modes: List[str] = Field(default=["text"])
    default_output_modes: List[str] = Field(default=["text"])


# ─────────────────────────────────────────────────────────────────────────────
# A2A Bridge Implementation
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class BridgeConfig:
    """Configuration for the A2A bridge."""
    event_bus_url: str = os.getenv("EVENT_BUS_URL", "http://localhost:8081")
    auth_service_url: str = os.getenv("AUTH_SERVICE_URL", "http://localhost:8080")
    jwt_secret: str = os.getenv("JWT_SECRET_KEY", "")
    max_concurrent_tasks: int = 100
    default_timeout: int = 300
    enable_streaming: bool = True


class A2ABridge:
    """
    A2A Protocol Bridge for ReliantAI multi-agent communication.
    
    Enables agents from different systems (APEX, Money, Citadel, Acropolis)
    to discover, communicate, and delegate tasks to each other.
    """

    def __init__(self, config: Optional[BridgeConfig] = None):
        self.config = config or BridgeConfig()
        self.agent_registry: Dict[str, AgentCard] = {}
        self.active_tasks: Dict[str, A2ATask] = {}
        self.subscribers: Dict[str, List[Callable]] = {}
        self._session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.default_timeout)
            )
        return self._session

    async def close(self):
        """Close the bridge and cleanup resources."""
        if self._session and not self._session.closed:
            await self._session.close()

    # ── Agent Registration ───────────────────────────────────────────────────

    async def register_agent(self, agent_card: AgentCard) -> str:
        """
        Register an agent in the A2A bridge.
        
        Args:
            agent_card: The agent's capabilities card
            
        Returns:
            agent_id: Unique identifier for the registered agent
        """
        agent_id = str(uuid.uuid4())
        
        async with self._lock:
            self.agent_registry[agent_id] = agent_card
        
        # Emit registration event
        await self._emit_event("agent.registered", {
            "agent_id": agent_id,
            "name": agent_card.name,
            "url": agent_card.url,
            "capabilities": [c.value for c in agent_card.capabilities],
        })
        
        return agent_id

    async def unregister_agent(self, agent_id: str) -> bool:
        """Unregister an agent from the bridge."""
        async with self._lock:
            if agent_id in self.agent_registry:
                del self.agent_registry[agent_id]
                return True
            return False

    async def get_agent(self, agent_id: str) -> Optional[AgentCard]:
        """Get an agent's card by ID."""
        return self.agent_registry.get(agent_id)

    async def list_agents(
        self,
        capability: Optional[AgentCapability] = None,
        skill_tag: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List registered agents with optional filtering.
        
        Args:
            capability: Filter by capability
            skill_tag: Filter by skill tag
            
        Returns:
            List of agent info dicts with id and card
        """
        results = []
        
        for agent_id, card in self.agent_registry.items():
            # Filter by capability
            if capability and capability not in card.capabilities:
                continue
            
            # Filter by skill tag
            if skill_tag:
                has_skill = any(
                    skill_tag in skill.tags for skill in card.skills
                )
                if not has_skill:
                    continue
            
            results.append({
                "agent_id": agent_id,
                "card": card.model_dump(),
            })
        
        return results

    async def find_agent_for_task(self, task_description: str) -> Optional[str]:
        """
        Find the best agent for a given task using skill matching.
        
        Args:
            task_description: Description of the task
            
        Returns:
            agent_id of the best matching agent, or None
        """
        # Simple keyword matching (could be enhanced with embeddings)
        task_lower = task_description.lower()
        
        best_match: Optional[str] = None
        best_score = 0
        
        for agent_id, card in self.agent_registry.items():
            score = 0
            for skill in card.skills:
                # Match skill name
                if skill.name.lower() in task_lower:
                    score += 3
                # Match skill tags
                for tag in skill.tags:
                    if tag.lower() in task_lower:
                        score += 2
                # Match skill examples
                for example in skill.examples:
                    if any(word in task_lower for word in example.lower().split()):
                        score += 1
            
            if score > best_score:
                best_score = score
                best_match = agent_id
        
        return best_match

    # ── Task Management ──────────────────────────────────────────────────────

    async def create_task(
        self,
        message: A2AMessage,
        target_agent_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> A2ATask:
        """
        Create a new A2A task.
        
        Args:
            message: The initial message/request
            target_agent_id: Optional specific agent to handle this task
            metadata: Additional task metadata
            
        Returns:
            Created A2ATask
        """
        task = A2ATask(
            message=message,
            metadata=metadata or {},
        )
        
        if target_agent_id:
            task.metadata["target_agent_id"] = target_agent_id
            agent_card = await self.get_agent(target_agent_id)
            if agent_card:
                task.agent_card = agent_card.model_dump()
        
        async with self._lock:
            self.active_tasks[task.task_id] = task
        
        await self._emit_event("task.created", {
            "task_id": task.task_id,
            "session_id": task.session_id,
            "target_agent": target_agent_id,
        })
        
        return task

    async def get_task(self, task_id: str) -> Optional[A2ATask]:
        """Get a task by ID."""
        return self.active_tasks.get(task_id)

    async def update_task_state(
        self,
        task_id: str,
        state: TaskState,
        message: Optional[str] = None,
    ) -> Optional[A2ATask]:
        """Update a task's state."""
        task = self.active_tasks.get(task_id)
        if not task:
            return None
        
        task.state = state
        task.updated_at = datetime.now(UTC)
        
        if message:
            task.history.append(A2AMessage(
                role=MessageRole.AGENT,
                content=message,
            ))
        
        await self._emit_event("task.state_changed", {
            "task_id": task_id,
            "new_state": state.value,
            "message": message,
        })
        
        return task

    async def add_artifact(
        self,
        task_id: str,
        artifact: A2AArtifact,
    ) -> Optional[A2ATask]:
        """Add an artifact to a task."""
        task = self.active_tasks.get(task_id)
        if not task:
            return None
        
        task.artifacts.append(artifact)
        task.updated_at = datetime.now(UTC)
        
        await self._emit_event("task.artifact_added", {
            "task_id": task_id,
            "artifact_id": artifact.artifact_id,
            "artifact_type": artifact.type.value,
        })
        
        return task

    # ── A2A Protocol Operations ────────────────────────────────────────────────

    async def send_task(
        self,
        target_agent_url: str,
        message: A2AMessage,
        session_id: Optional[str] = None,
    ) -> A2ATask:
        """
        Send a task to a remote agent via A2A protocol.
        
        Args:
            target_agent_url: URL of the target agent's A2A endpoint
            message: The message to send
            session_id: Optional session ID for continuity
            
        Returns:
            A2ATask with the remote agent's response
        """
        session = await self._get_session()
        
        payload = {
            "message": message.model_dump(),
            "session_id": session_id,
        }
        
        async with session.post(
            f"{target_agent_url}/a2a/tasks/send",
            json=payload,
            headers={"Content-Type": "application/json"},
        ) as response:
            response.raise_for_status()
            data = await response.json()
            
            return A2ATask(**data)

    async def send_task_streaming(
        self,
        target_agent_url: str,
        message: A2AMessage,
        session_id: Optional[str] = None,
    ) -> AsyncIterator[A2AStatusUpdate]:
        """
        Send a task with streaming updates.
        
        Yields status updates as they arrive from the remote agent.
        """
        session = await self._get_session()
        
        payload = {
            "message": message.model_dump(),
            "session_id": session_id,
        }
        
        async with session.post(
            f"{target_agent_url}/a2a/tasks/sendSubscribe",
            json=payload,
            headers={"Content-Type": "application/json"},
        ) as response:
            response.raise_for_status()
            
            # Handle SSE stream
            async for line in response.content:
                line = line.decode("utf-8").strip()
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    yield A2AStatusUpdate(**data)

    async def get_task_status(
        self,
        target_agent_url: str,
        task_id: str,
    ) -> A2ATask:
        """Get the current status of a remote task."""
        session = await self._get_session()
        
        async with session.get(
            f"{target_agent_url}/a2a/tasks/{task_id}",
        ) as response:
            response.raise_for_status()
            data = await response.json()
            return A2ATask(**data)

    async def cancel_task(
        self,
        target_agent_url: str,
        task_id: str,
    ) -> bool:
        """Cancel a remote task."""
        session = await self._get_session()
        
        async with session.post(
            f"{target_agent_url}/a2a/tasks/{task_id}/cancel",
        ) as response:
            return response.status == 200

    # ── Agent Responder ────────────────────────────────────────────────────────

    async def handle_incoming_task(
        self,
        task: A2ATask,
        handler: Callable[[A2ATask], asyncio.Future[A2ATask]],
    ) -> A2ATask:
        """
        Handle an incoming A2A task.
        
        Args:
            task: The incoming task
            handler: Async function to process the task
            
        Returns:
            Updated task with results
        """
        # Update state to working
        await self.update_task_state(task.task_id, TaskState.WORKING)
        
        try:
            # Process the task
            result_task = await handler(task)
            
            # Mark as completed
            await self.update_task_state(
                result_task.task_id,
                TaskState.COMPLETED,
                "Task completed successfully",
            )
            
            return result_task
            
        except Exception as e:
            # Mark as failed
            await self.update_task_state(
                task.task_id,
                TaskState.FAILED,
                f"Task failed: {str(e)}",
            )
            
            # Add error artifact
            error_artifact = A2AArtifact(
                type=ArtifactType.ERROR,
                name="error",
                content={"error": str(e), "type": type(e).__name__},
            )
            await self.add_artifact(task.task_id, error_artifact)
            
            raise

    # ── Event Bus Integration ────────────────────────────────────────────────

    async def _emit_event(self, event_type: str, payload: Dict[str, Any]):
        """Emit an event to the Event Bus."""
        try:
            session = await self._get_session()
            
            event = {
                "event_type": event_type,
                "timestamp": datetime.now(UTC).isoformat(),
                "payload": payload,
            }
            
            await session.post(
                f"{self.config.event_bus_url}/publish",
                json=event,
            )
        except Exception as e:
            # Log but don't fail if event bus is unavailable
            print(f"[A2ABridge] Failed to emit event {event_type}: {e}")

    # ── Cross-System Delegation ──────────────────────────────────────────────

    async def delegate_to_apex(
        self,
        task: str,
        context: Dict[str, Any],
        trace_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Delegate a task to the APEX agent system."""
        apex_url = os.getenv("APEX_AGENTS_URL", "http://localhost:8001")
        
        session = await self._get_session()
        
        payload = {
            "task": task,
            "context": context,
            "trace_id": trace_id or str(uuid.uuid4()),
        }
        
        async with session.post(
            f"{apex_url}/workflow/run",
            json=payload,
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def delegate_to_money(
        self,
        sms_body: str,
        from_phone: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Delegate an HVAC dispatch task to the Money system."""
        money_url = os.getenv("MONEY_API_URL", "http://localhost:8000")
        
        session = await self._get_session()
        
        payload = {
            "Body": sms_body,
            "From": from_phone or "+1234567890",
        }
        
        async with session.post(
            f"{money_url}/sms",
            data=payload,  # Money expects form data
        ) as response:
            response.raise_for_status()
            return await response.json()

    async def delegate_to_citadel(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Delegate to Citadel's NL agent service."""
        citadel_url = os.getenv("CITADEL_URL", "http://localhost:8002")
        
        session = await self._get_session()
        
        payload = {
            "model": model or "gemini-2.0-flash",
            "messages": messages,
        }
        
        async with session.post(
            f"{citadel_url}/v1/chat/completions",
            json=payload,
        ) as response:
            response.raise_for_status()
            return await response.json()


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI Endpoint Helpers
# ─────────────────────────────────────────────────────────────────────────────

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse


def create_a2a_routes(app: FastAPI, bridge: A2ABridge) -> None:
    """
    Register A2A protocol routes on a FastAPI app.
    
    Usage:
        app = FastAPI()
        bridge = A2ABridge()
        create_a2a_routes(app, bridge)
    """

    @app.get("/a2a/agent")
    async def get_agent_card() -> Dict[str, Any]:
        """Return this agent's capabilities card."""
        # This should be overridden with actual agent info
        return {
            "name": "ReliantAI-A2A-Bridge",
            "description": "Multi-agent orchestration bridge",
            "version": "1.0.0",
            "capabilities": ["streaming", "state_transitions"],
        }

    @app.post("/a2a/tasks/send")
    async def send_task_endpoint(request: Dict[str, Any]) -> Dict[str, Any]:
        """Receive a task (non-streaming)."""
        message = A2AMessage(**request.get("message", {}))
        
        task = await bridge.create_task(
            message=message,
            metadata={"session_id": request.get("session_id")},
        )
        
        # This should trigger actual processing
        return task.model_dump()

    @app.get("/a2a/tasks/{task_id}")
    async def get_task_endpoint(task_id: str) -> Dict[str, Any]:
        """Get task status."""
        task = await bridge.get_task(task_id)
        if not task:
            raise HTTPException(404, f"Task {task_id} not found")
        return task.model_dump()

    @app.post("/a2a/tasks/{task_id}/cancel")
    async def cancel_task_endpoint(task_id: str) -> Dict[str, Any]:
        """Cancel a task."""
        task = await bridge.update_task_state(task_id, TaskState.CANCELED)
        if not task:
            raise HTTPException(404, f"Task {task_id} not found")
        return {"success": True, "task_id": task_id}


# ─────────────────────────────────────────────────────────────────────────────
# Singleton Bridge Instance
# ─────────────────────────────────────────────────────────────────────────────

_bridge_instance: Optional[A2ABridge] = None


def get_a2a_bridge() -> A2ABridge:
    """Get or create the global A2A bridge instance."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = A2ABridge()
    return _bridge_instance


async def init_a2a_bridge() -> A2ABridge:
    """Initialize the A2A bridge and return it."""
    bridge = get_a2a_bridge()
    
    # Register built-in agents
    await bridge.register_agent(AgentCard(
        name="APEX-Orchestrator",
        description="4-layer agent workflow system",
        url=os.getenv("APEX_AGENTS_URL", "http://localhost:8001"),
        version="1.0.0",
        capabilities=[AgentCapability.STREAMING, AgentCapability.STATE_TRANSITIONS],
        skills=[
            AgentSkill(
                id="layer1-analysis",
                name="Strategic Analysis",
                description="Theory of Mind + Data Model Planning",
                tags=["analysis", "planning", "strategy"],
            ),
            AgentSkill(
                id="layer2-calibration",
                name="Uncertainty Calibration",
                description="Probabilistic uncertainty quantification",
                tags=["calibration", "uncertainty", "quality"],
            ),
            AgentSkill(
                id="layer3-dispatch",
                name="Specialist Dispatch",
                description="Research, Creative, Analytics, Sales",
                tags=["research", "creative", "analytics", "sales"],
            ),
        ],
    ))
    
    await bridge.register_agent(AgentCard(
        name="Money-HVAC-Dispatch",
        description="5-agent CrewAI HVAC emergency dispatch",
        url=os.getenv("MONEY_API_URL", "http://localhost:8000"),
        version="1.0.0",
        capabilities=[AgentCapability.STATE_TRANSITIONS],
        skills=[
            AgentSkill(
                id="hvac-triage",
                name="HVAC Emergency Triage",
                description="Classify HVAC emergencies by urgency",
                tags=["hvac", "emergency", "triage"],
            ),
            AgentSkill(
                id="dispatch-optimization",
                name="Dispatch Optimization",
                description="Route to best available technician",
                tags=["dispatch", "scheduling", "optimization"],
            ),
        ],
    ))
    
    await bridge.register_agent(AgentCard(
        name="Citadel-NL-Agent",
        description="Natural language agent with tool routing",
        url=os.getenv("CITADEL_URL", "http://localhost:8002"),
        version="1.0.0",
        capabilities=[AgentCapability.STREAMING],
        skills=[
            AgentSkill(
                id="nl-chat",
                name="Natural Language Chat",
                description="Conversational AI with tool access",
                tags=["chat", "nlp", "conversation"],
            ),
            AgentSkill(
                id="tool-routing",
                name="Tool Routing",
                description="Intelligent tool selection and execution",
                tags=["tools", "routing", "execution"],
            ),
        ],
    ))
    
    return bridge


# ─────────────────────────────────────────────────────────────────────────────
# CLI for testing
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    
    async def main():
        bridge = await init_a2a_bridge()
        
        if len(sys.argv) < 2:
            print("Usage: a2a_bridge.py <command> [args...]")
            print("Commands: list-agents, find-agent, create-task")
            return
        
        cmd = sys.argv[1]
        
        if cmd == "list-agents":
            agents = await bridge.list_agents()
            print(f"Registered agents: {len(agents)}")
            for agent in agents:
                print(f"  - {agent['card']['name']} ({agent['agent_id'][:8]}...)")
        
        elif cmd == "find-agent":
            if len(sys.argv) < 3:
                print("Usage: find-agent <task description>")
                return
            task_desc = sys.argv[2]
            agent_id = await bridge.find_agent_for_task(task_desc)
            if agent_id:
                card = await bridge.get_agent(agent_id)
                print(f"Best match: {card.name} ({agent_id[:8]}...)")
            else:
                print("No suitable agent found")
        
        elif cmd == "create-task":
            message = A2AMessage(
                role=MessageRole.USER,
                content=" ".join(sys.argv[2:]) if len(sys.argv) > 2 else "Hello A2A!",
            )
            task = await bridge.create_task(message)
            print(f"Created task: {task.task_id}")
        
        await bridge.close()
    
    asyncio.run(main())

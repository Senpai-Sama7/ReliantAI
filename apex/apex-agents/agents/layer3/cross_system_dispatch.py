# apex-agents/agents/layer3/cross_system_dispatch.py
"""
APEX Layer 3 Cross-System Dispatcher

Extends the standard Layer 3 dispatcher with A2A protocol integration,
enabling specialist agents to delegate tasks to other ReliantAI systems:
- Money (HVAC dispatch)
- Citadel (NL agent)
- Acropolis (polyglot orchestrator)

This enables the full 4-system integration where APEX agents can:
1. Route HVAC emergencies to Money's 5-agent CrewAI
2. Route conversational tasks to Citadel's NL agent
3. Route complex polyglot tasks to Acropolis
4. Use MCP tools for browser, computer, and code execution
"""

from __future__ import annotations

import os
import sys
import time
from typing import TypedDict, Any, Dict, List, Optional
from uuid import uuid4
from dataclasses import dataclass
from enum import Enum

# Add integration dir to path for A2A bridge import
sys.path.insert(0, str(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "integration")))

try:
    from a2a_bridge import A2ABridge
    from cross_system_orchestrator import (
        CrossSystemOrchestrator, SystemType, WorkflowDefinition, WorkflowStep
    )
    A2A_AVAILABLE = True
except ImportError as e:
    A2A_AVAILABLE = False
    print(f"[CrossSystemDispatch] A2A bridge not available: {e}")

from agents.layer3.dispatcher import dispatch as standard_dispatch, DispatchResult


# ─────────────────────────────────────────────────────────────────────────────
# Cross-System Task Types
# ─────────────────────────────────────────────────────────────────────────────

class CrossSystemType(str, Enum):
    """Types of cross-system delegation."""
    HVAC_DISPATCH = "hvac_dispatch"
    CHAT_COMPLETION = "chat_completion"
    TOOL_EXECUTION = "tool_execution"
    POLYGLOT_TASK = "polyglot_task"


@dataclass
class CrossSystemTask:
    """A task to be delegated to another system."""
    task_type: CrossSystemType
    target_system: SystemType
    parameters: Dict[str, Any]
    priority: int = 1
    timeout_seconds: int = 300


# ─────────────────────────────────────────────────────────────────────────────
# Enhanced Dispatch Result
# ─────────────────────────────────────────────────────────────────────────────

class EnhancedDispatchResult(TypedDict):
    """Extended dispatch result with cross-system integration."""
    task_type: str
    specialists: List[str]
    results: Dict[str, Any]
    errors: Dict[str, str]
    confidence: float
    # Cross-system additions
    cross_system_calls: List[Dict[str, Any]]
    systems_contacted: List[str]
    execution_time_ms: float
    trace_id: str


# ─────────────────────────────────────────────────────────────────────────────
# Cross-System Dispatcher
# ─────────────────────────────────────────────────────────────────────────────

class CrossSystemDispatcher:
    """
    Extended Layer 3 dispatcher with cross-system capabilities.
    
    This dispatcher can:
    1. Run standard APEX specialists (research, creative, analytics, sales)
    2. Delegate to Money for HVAC emergencies
    3. Delegate to Citadel for conversational tasks
    4. Use MCP tools for browser/computer/code execution
    5. Coordinate multi-system workflows
    """

    def __init__(self):
        self.orchestrator: Optional[CrossSystemOrchestrator] = None
        self.a2a_bridge: Optional[A2ABridge] = None
        self._initialized = False

    async def initialize(self):
        """Initialize the cross-system dispatcher."""
        if self._initialized:
            return
        
        if A2A_AVAILABLE:
            self.orchestrator = CrossSystemOrchestrator()
            await self.orchestrator.initialize()
            self.a2a_bridge = self.orchestrator.a2a_bridge
        
        self._initialized = True

    async def shutdown(self):
        """Cleanup resources."""
        if self.orchestrator:
            await self.orchestrator.shutdown()

    def _detect_cross_system_need(self, task: str, context: dict) -> Optional[CrossSystemTask]:
        """
        Detect if a task should be delegated to another system.
        
        Returns a CrossSystemTask if delegation is needed, None otherwise.
        """
        task_lower = task.lower()
        
        # HVAC-related tasks -> Money
        hvac_keywords = [
            "hvac", "ac ", "air conditioning", "heating", "cooling",
            "thermostat", "furnace", "heat pump", "compressor",
            "refrigerant", "no heat", "no cool", "too hot", "too cold",
            "hvac emergency", "ac emergency", "ac repair", "furnace repair",
            "houston", "dispatch", "technician", "service call",
        ]
        if any(kw in task_lower for kw in hvac_keywords):
            return CrossSystemTask(
                task_type=CrossSystemType.HVAC_DISPATCH,
                target_system=SystemType.MONEY,
                parameters={"sms_body": task, "context": context},
                priority=1,  # HVAC emergencies are high priority
            )
        
        # Chat/conversational tasks -> Citadel
        chat_keywords = [
            "chat", "talk to", "ask you", "can you explain", "what is",
            "how does", "tell me about", "describe", "summarize",
            "translate", "convert", "help me understand",
        ]
        if any(kw in task_lower for kw in chat_keywords):
            return CrossSystemTask(
                task_type=CrossSystemType.CHAT_COMPLETION,
                target_system=SystemType.CITADEL,
                parameters={
                    "messages": [{"role": "user", "content": task}],
                    "context": context,
                },
            )
        
        # Browser automation needed -> MCP tool
        browser_keywords = [
            "browse", "visit website", "go to", "scrape", "extract from",
            "screenshot of", "click on", "fill form", "web page",
        ]
        if any(kw in task_lower for kw in browser_keywords):
            # Extract URL if present
            import re
            url_match = re.search(r'https?://[^\s<>"{}|\\^`\[\]]+', task)
            if url_match:
                return CrossSystemTask(
                    task_type=CrossSystemType.TOOL_EXECUTION,
                    target_system=SystemType.APEX,  # MCP is part of APEX
                    parameters={
                        "tool": "browser_navigate",
                        "arguments": {"url": url_match.group(0)},
                    },
                )
        
        # Code execution needed -> MCP tool
        code_keywords = [
            "execute python", "run python", "execute javascript",
            "run code", "calculate", "compute", "script",
        ]
        if any(kw in task_lower for kw in code_keywords):
            # Extract code block if present
            code_block = None
            if "```python" in task:
                code_block = task.split("```python")[1].split("```")[0].strip()
            elif "```javascript" in task:
                code_block = task.split("```javascript")[1].split("```")[0].strip()
            elif "```js" in task:
                code_block = task.split("```js")[1].split("```")[0].strip()
            
            if code_block:
                tool = "code_execute_python" if "python" in task_lower else "code_execute_javascript"
                return CrossSystemTask(
                    task_type=CrossSystemType.TOOL_EXECUTION,
                    target_system=SystemType.APEX,
                    parameters={
                        "tool": tool,
                        "arguments": {"code": code_block},
                    },
                )
        
        return None

    async def dispatch(
        self,
        task: str,
        context: dict,
        prior_summary: str,
        task_type: str | None = None,
        trace_id: str | None = None,
        enable_cross_system: bool = True,
    ) -> EnhancedDispatchResult:
        """
        Enhanced dispatch with cross-system capabilities.
        
        Args:
            task: Task description
            context: Context dictionary
            prior_summary: Summary from previous layers
            task_type: Optional task type hint
            trace_id: Trace ID for logging
            enable_cross_system: Whether to enable cross-system delegation
            
        Returns:
            EnhancedDispatchResult with cross-system integration
        """
        start_time = time.time()
        
        tid = trace_id or str(uuid4())
        cross_system_calls: List[Dict[str, Any]] = []
        systems_contacted: List[str] = []
        
        # Check if task should go to another system
        if enable_cross_system and A2A_AVAILABLE and self.orchestrator:
            cross_task = self._detect_cross_system_need(task, context)
            
            if cross_task:
                try:
                    if cross_task.task_type == CrossSystemType.HVAC_DISPATCH:
                        result = await self.orchestrator.execute_on_money(
                            cross_task.parameters["sms_body"],
                        )
                        systems_contacted.append("money")
                        cross_system_calls.append({
                            "type": "hvac_dispatch",
                            "success": result.success,
                            "data": result.data,
                        })
                        
                        # If successful, return early
                        if result.success:
                            elapsed_ms = (time.time() - start_time) * 1000
                            return EnhancedDispatchResult(
                                task_type="hvac_dispatch",
                                specialists=["money_crewai"],
                                results={"hvac_dispatch": result.data},
                                errors={} if result.success else {"money": result.error},
                                confidence=0.95 if result.success else 0.3,
                                cross_system_calls=cross_system_calls,
                                systems_contacted=systems_contacted,
                                execution_time_ms=elapsed_ms,
                                trace_id=tid,
                            )
                    
                    elif cross_task.task_type == CrossSystemType.CHAT_COMPLETION:
                        result = await self.orchestrator.execute_on_citadel(
                            cross_task.parameters["messages"],
                        )
                        systems_contacted.append("citadel")
                        cross_system_calls.append({
                            "type": "chat_completion",
                            "success": result.success,
                            "data": result.data,
                        })
                        
                        elapsed_ms = (time.time() - start_time) * 1000
                        return EnhancedDispatchResult(
                            task_type="chat_completion",
                            specialists=["citadel_nl_agent"],
                            results={"chat": result.data},
                            errors={} if result.success else {"citadel": result.error},
                            confidence=0.9 if result.success else 0.3,
                            cross_system_calls=cross_system_calls,
                            systems_contacted=systems_contacted,
                            execution_time_ms=elapsed_ms,
                            trace_id=tid,
                        )
                    
                    elif cross_task.task_type == CrossSystemType.TOOL_EXECUTION:
                        result = await self.orchestrator.execute_mcp_tool(
                            cross_task.parameters["tool"],
                            cross_task.parameters["arguments"],
                        )
                        systems_contacted.append("apex_mcp")
                        cross_system_calls.append({
                            "type": "mcp_tool",
                            "tool": cross_task.parameters["tool"],
                            "success": result.success,
                            "data": result.data,
                        })
                        
                        elapsed_ms = (time.time() - start_time) * 1000
                        return EnhancedDispatchResult(
                            task_type="tool_execution",
                            specialists=["mcp_tool_bus"],
                            results={"tool_result": result.data},
                            errors={} if result.success else {"mcp": result.error},
                            confidence=0.9 if result.success else 0.3,
                            cross_system_calls=cross_system_calls,
                            systems_contacted=systems_contacted,
                            execution_time_ms=elapsed_ms,
                            trace_id=tid,
                        )
                        
                except Exception as e:
                    cross_system_calls.append({
                        "type": "error",
                        "error": str(e),
                    })
                    # Fall through to standard dispatch on error
        
        # Standard APEX dispatch
        standard_result = await standard_dispatch(
            task=task,
            context=context,
            prior_summary=prior_summary,
            task_type=task_type,
            trace_id=tid,
        )
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        return EnhancedDispatchResult(
            task_type=standard_result["task_type"],
            specialists=standard_result["specialists"],
            results=standard_result["results"],
            errors=standard_result["errors"],
            confidence=standard_result["confidence"],
            cross_system_calls=cross_system_calls,
            systems_contacted=systems_contacted,
            execution_time_ms=elapsed_ms,
            trace_id=tid,
        )

    async def create_multi_system_workflow(
        self,
        task: str,
        context: dict,
    ) -> Optional[WorkflowDefinition]:
        """
        Create a multi-system workflow for complex tasks.
        
        Example: HVAC emergency that needs both dispatch and customer communication
        """
        if not A2A_AVAILABLE or not self.orchestrator:
            return None
        
        task_lower = task.lower()
        
        # HVAC emergency workflow: Money dispatch + Citadel customer communication
        if any(kw in task_lower for kw in ["hvac", "ac ", "emergency"]):
            return WorkflowDefinition(
                name="HVAC Emergency Response",
                description="Coordinate HVAC dispatch with customer communication",
                steps=[
                    WorkflowStep(
                        name="dispatch_assessment",
                        system=SystemType.MONEY,
                        operation="sms.dispatch",
                        parameters={"sms_body": task},
                    ),
                    WorkflowStep(
                        name="customer_followup",
                        system=SystemType.CITADEL,
                        operation="chat.completion",
                        parameters={
                            "messages": [
                                {"role": "system", "content": "You are a helpful HVAC assistant."},
                                {"role": "user", "content": f"Acknowledge this emergency and provide reassurance: {task}"},
                            ]
                        },
                        depends_on=["dispatch_assessment"],
                    ),
                ],
            )
        
        # Research workflow: APEX research + browser scraping + analysis
        if any(kw in task_lower for kw in ["research", "find", "look up"]):
            return WorkflowDefinition(
                name="Multi-Source Research",
                description="Research using APEX specialists and web scraping",
                steps=[
                    WorkflowStep(
                        name="web_search",
                        system=SystemType.APEX,
                        operation="mcp.tool",
                        parameters={"tool": "brave_search", "arguments": {"query": task}},
                    ),
                    WorkflowStep(
                        name="apex_analysis",
                        system=SystemType.APEX,
                        operation="workflow.run",
                        parameters={"task": f"Analyze: {task}", "context": context},
                        depends_on=["web_search"],
                    ),
                ],
            )
        
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Global Dispatcher Instance
# ─────────────────────────────────────────────────────────────────────────────

_dispatcher_instance: Optional[CrossSystemDispatcher] = None


def get_cross_system_dispatcher() -> CrossSystemDispatcher:
    """Get or create the global cross-system dispatcher."""
    global _dispatcher_instance
    if _dispatcher_instance is None:
        _dispatcher_instance = CrossSystemDispatcher()
    return _dispatcher_instance


async def cross_system_dispatch(
    task: str,
    context: dict,
    prior_summary: str,
    task_type: str | None = None,
    trace_id: str | None = None,
    enable_cross_system: bool = True,
) -> EnhancedDispatchResult:
    """
    Convenience function for cross-system dispatch.
    
    Usage:
        result = await cross_system_dispatch(
            "My AC is broken in Houston",
            context={},
            prior_summary="",
        )
    """
    dispatcher = get_cross_system_dispatcher()
    
    if not dispatcher._initialized:
        await dispatcher.initialize()
    
    return await dispatcher.dispatch(
        task=task,
        context=context,
        prior_summary=prior_summary,
        task_type=task_type,
        trace_id=trace_id,
        enable_cross_system=enable_cross_system,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Backwards compatibility - update standard dispatch export
# ─────────────────────────────────────────────────────────────────────────────

async def dispatch(
    task: str,
    context: dict,
    prior_summary: str,
    task_type: str | None = None,
    trace_id: str | None = None,
) -> DispatchResult:
    """
    Drop-in replacement for standard dispatch with cross-system support.
    
    This maintains backwards compatibility while adding cross-system capabilities.
    """
    result = await cross_system_dispatch(
        task=task,
        context=context,
        prior_summary=prior_summary,
        task_type=task_type,
        trace_id=trace_id,
        enable_cross_system=True,
    )
    
    # Return in standard format for backwards compatibility
    return DispatchResult(
        task_type=result["task_type"],
        specialists=result["specialists"],
        results=result["results"],
        errors=result["errors"],
        confidence=result["confidence"],
    )

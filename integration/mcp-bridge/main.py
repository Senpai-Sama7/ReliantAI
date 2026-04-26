"""
ReliantAI MCP Bridge — Model Context Protocol Server
=====================================================
Exposes all platform microservices as discoverable, callable tools for AI agents.
Implements the Model Context Protocol (MCP) over HTTP/SSE for real-time tool access.

Design: Every service registers its capabilities. The AI queries available tools,
receives schemas, and calls them with validated parameters. All calls are audited.
"""

import asyncio
import json
import os
import time
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

import httpx
import secrets as _secrets

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
import redis.asyncio as aioredis

app = FastAPI(title="ReliantAI MCP Bridge", version="1.0.0")

CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "http://localhost,http://localhost:3000,http://localhost:8085")
_origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]
if "*" not in _origins:
    from fastapi.middleware.cors import CORSMiddleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ── Configuration ───────────────────────────────────────────────
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
MCP_API_KEY = os.environ.get("MCP_API_KEY", "")
REGISTRY_URL = os.environ.get("REGISTRY_URL", "http://service-registry:8082")
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

_redis_pool: aioredis.Redis | None = None

# ── Data Models ─────────────────────────────────────────────────

class MCPToolParameter(BaseModel):
    name: str
    type: str = "string"
    description: str
    required: bool = True
    default: Optional[Any] = None
    enum: Optional[List[str]] = None

class MCPTool(BaseModel):
    name: str
    description: str
    service: str
    endpoint: str
    method: str = "POST"
    parameters: List[MCPToolParameter]
    returns: Dict[str, Any]
    examples: List[Dict[str, Any]] = []
    rate_limit: str = "100/min"
    timeout_ms: int = 30000

class MCPToolCall(BaseModel):
    tool: str
    parameters: Dict[str, Any]
    correlation_id: Optional[str] = None
    requesting_agent: Optional[str] = None

class MCPToolResult(BaseModel):
    tool: str
    status: str  # success, error, timeout, rate_limited
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: int = 0
    correlation_id: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class MCPDiscoveryRequest(BaseModel):
    service: Optional[str] = None  # Filter by service
    capability: Optional[str] = None  # Filter by capability tag

# ── In-Memory Registry (backed by Redis) ────────────────────────

_tools: Dict[str, MCPTool] = {}
_tool_history: List[Dict] = []

async def _get_redis() -> aioredis.Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _redis_pool

async def verify_api_key(api_key: str = Security(_api_key_header)) -> str:
    if not MCP_API_KEY:
        raise HTTPException(status_code=503, detail="MCP API key not configured. Set MCP_API_KEY environment variable.")
    if not api_key or not _secrets.compare_digest(api_key, MCP_API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key


def _validate_endpoint(endpoint: str) -> tuple[bool, str]:
    """Validate endpoint to prevent SSRF attacks using ipaddress module."""
    import ipaddress
    from urllib.parse import urlparse
    parsed = urlparse(endpoint)
    
    # Block dangerous schemes
    if parsed.scheme.lower() not in ('http', 'https'):
        return False, f"Invalid scheme: {parsed.scheme}. Only http/https allowed."
    
    if not parsed.hostname:
        return False, "No hostname in endpoint"
    
    # Block localhost
    hostname_lower = parsed.hostname.lower()
    if hostname_lower in ('localhost', '127.0.0.1', '0.0.0.0', '::1'):
        return False, "Localhost addresses not allowed."
    
    # Block link-local (169.254.0.0/16) and metadata endpoints
    if hostname_lower.startswith(('169.254.', 'metadata.google.', 'metadata.azure.')):
        return False, "Metadata/link-local endpoints not allowed."
    
    # Validate IP using ipaddress module
    try:
        ip = ipaddress.ip_address(parsed.hostname)
        if ip.is_loopback or ip.is_link_local or ip.is_private:
            return False, f"Private/loopback IP not allowed: {ip}"
    except ValueError:
        # Not an IP address, check if hostname resolves to private (skip DNS for now)
        pass
    
    return True, "OK"

# ── Core MCP Endpoints ──────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "mcp-bridge", "tools_registered": len(_tools)}

@app.get("/mcp/tools", response_model=List[MCPTool])
async def list_tools(
    service: Optional[str] = None,
    capability: Optional[str] = None
):
    """Discover available tools. Filter by service or capability."""
    tools = list(_tools.values())
    if service:
        tools = [t for t in tools if t.service == service]
    if capability:
        tools = [t for t in tools if capability.lower() in t.description.lower()]
    return tools

@app.post("/mcp/tools/call", response_model=MCPToolResult)
async def call_tool(call: MCPToolCall, background: BackgroundTasks, _auth: str = Depends(verify_api_key)):
    """Execute a tool call against the target service."""
    start = time.time()
    
    tool = _tools.get(call.tool)
    if not tool:
        return MCPToolResult(
            tool=call.tool,
            status="error",
            error=f"Tool '{call.tool}' not found. Available: {list(_tools.keys())}",
            execution_time_ms=0,
            correlation_id=call.correlation_id
        )
    
    # Validate parameters
    required_params = {p.name for p in tool.parameters if p.required}
    provided_params = set(call.parameters.keys())
    missing = required_params - provided_params
    if missing:
        return MCPToolResult(
            tool=call.tool,
            status="error",
            error=f"Missing required parameters: {missing}",
            execution_time_ms=0,
            correlation_id=call.correlation_id
        )
    
    # Execute the tool call
    try:
        # Resolve URL template with parameters (copy params to avoid modifying original)
        resolved_url = tool.endpoint
        params_copy = dict(call.parameters)
        for param_name in list(params_copy.keys()):
            placeholder = f"{{{param_name}}}"
            if placeholder in resolved_url:
                resolved_url = resolved_url.replace(placeholder, str(params_copy[param_name]))
                del params_copy[param_name]
        # Determine the appropriate API key based on the target service
        service_upper = tool.service.upper().replace("-", "_")
        api_key = ""
        if service_upper == "MONEY":
            api_key = os.environ.get("DISPATCH_API_KEY", os.environ.get("API_KEY", ""))
        elif service_upper == "INTEGRATION":
            api_key = os.environ.get("EVENT_BUS_API_KEY", "")
        elif service_upper == "RELIANT_OS":
            api_key = os.environ.get("OS_API_KEY", "")
        else:
            api_key = os.environ.get(f"{service_upper}_API_KEY", os.environ.get("API_KEY", ""))
            
        headers = {"X-API-Key": api_key} if api_key else {}
        
        async with httpx.AsyncClient(timeout=tool.timeout_ms / 1000, headers=headers) as client:
            if tool.method.upper() == "GET":
                response = await client.get(resolved_url, params=params_copy)
            else:
                response = await client.post(resolved_url, json=params_copy)
            
            response.raise_for_status()
            result_data = response.json()
            
        exec_time = int((time.time() - start) * 1000)
        
        # Log to history (async)
        background.add_task(_log_tool_call, call, "success", exec_time, result_data)
        
        return MCPToolResult(
            tool=call.tool,
            status="success",
            result=result_data,
            execution_time_ms=exec_time,
            correlation_id=call.correlation_id
        )
        
    except httpx.TimeoutException:
        exec_time = int((time.time() - start) * 1000)
        background.add_task(_log_tool_call, call, "timeout", exec_time, None)
        return MCPToolResult(
            tool=call.tool,
            status="timeout",
            error=f"Tool call timed out after {tool.timeout_ms}ms",
            execution_time_ms=exec_time,
            correlation_id=call.correlation_id
        )
    except Exception as e:
        exec_time = int((time.time() - start) * 1000)
        background.add_task(_log_tool_call, call, "error", exec_time, None)
        return MCPToolResult(
            tool=call.tool,
            status="error",
            error=str(e),
            execution_time_ms=exec_time,
            correlation_id=call.correlation_id
        )

@app.get("/mcp/tools/history")
async def tool_history(limit: int = 50):
    """Get recent tool execution history for auditing."""
    return _tool_history[-limit:]

@app.post("/mcp/register")
async def register_tool(tool: MCPTool, _auth: str = Depends(verify_api_key)):
    # Validate endpoint before registration
    is_valid, reason = _validate_endpoint(tool.endpoint)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Invalid endpoint: {reason}")
    
    _tools[tool.name] = tool
    try:
        r = await _get_redis()
        await r.setex(f"mcp:tool:{tool.name}", 3600, json.dumps(tool.dict()))
        await r.publish("mcp:registry:update", json.dumps({"tool": tool.name, "action": "register"}))
    except Exception:
        pass
    return {"status": "registered", "tool": tool.name}

@app.post("/mcp/unregister")
async def unregister_tool(name: str, _auth: str = Depends(verify_api_key)):
    """Unregister a tool (called by services on shutdown)."""
    if name in _tools:
        del _tools[name]
    return {"status": "unregistered", "tool": name}

# ── Internal ───────────────────────────────────────────────────

async def _log_tool_call(call: MCPToolCall, status: str, exec_time: int, result: Any):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tool": call.tool,
        "parameters": call.parameters,
        "status": status,
        "execution_time_ms": exec_time,
        "correlation_id": call.correlation_id,
        "requesting_agent": call.requesting_agent,
    }
    _tool_history.append(entry)
    if len(_tool_history) > 1000:
        _tool_history.pop(0)
    
    try:
        r = await _get_redis()
        await r.publish("events:mcp:tool_call", json.dumps(entry))
    except Exception:
        pass

# ── Bootstrap: Register Built-in Platform Tools ─────────────────

async def _bootstrap_tools():
    """Register all known ReliantAI platform tools on startup."""
    built_ins = [
        MCPTool(
            name="money.get_dispatches",
            description="Retrieve HVAC dispatch jobs from the Money service. Filter by status, priority, or technician.",
            service="money",
            endpoint="http://money:8000/dispatches",
            method="GET",
            parameters=[
                MCPToolParameter(name="status", type="string", description="Filter by dispatch status: pending, dispatched, en_route, on_site, completed, cancelled", required=False),
                MCPToolParameter(name="priority", type="string", description="Filter by priority: P0-LIFE, P1, P2, P3, P4", required=False),
                MCPToolParameter(name="limit", type="integer", description="Max results to return", required=False, default=20),
            ],
            returns={"type": "array", "items": {"type": "object"}},
            examples=[{"status": "dispatched", "limit": 10}],
        ),
        MCPTool(
            name="money.create_dispatch",
            description="Create a new HVAC dispatch job. Triggers CrewAI triage automatically.",
            service="money",
            endpoint="http://money:8000/dispatch",
            method="POST",
            parameters=[
                MCPToolParameter(name="lead_name", type="string", description="Customer name", required=True),
                MCPToolParameter(name="phone", type="string", description="Customer phone number", required=True),
                MCPToolParameter(name="issue", type="string", description="Description of the HVAC issue", required=True),
                MCPToolParameter(name="source", type="string", description="Lead source: Inbound SMS, Inbound Call, Web Form", required=False, default="AI Agent"),
            ],
            returns={"type": "object", "properties": {"dispatch_id": {"type": "string"}, "status": {"type": "string"}}},
        ),
        MCPTool(
            name="growthengine.find_leads",
            description="Search Google Places for home service businesses matching criteria. Returns prospects with ratings, review counts, and website presence.",
            service="growthengine",
            endpoint="http://growthengine:8003/api/prospect/scan",
            method="POST",
            parameters=[
                MCPToolParameter(name="lat", type="number", description="Latitude of search center", required=True),
                MCPToolParameter(name="lng", type="number", description="Longitude of search center", required=True),
                MCPToolParameter(name="keyword", type="string", description="Business type keyword: HVAC, plumbing, electrician, roofing, dentist", required=True),
                MCPToolParameter(name="radius", type="integer", description="Search radius in meters", required=False, default=5000),
                MCPToolParameter(name="min_rating", type="number", description="Minimum Google rating (1-5)", required=False, default=4.0),
            ],
            returns={"type": "array", "items": {"type": "object"}},
        ),
        MCPTool(
            name="growthengine.send_outreach",
            description="Send personalized SMS pitch to a prospect via Twilio through the Money service.",
            service="growthengine",
            endpoint="http://growthengine:8003/api/prospect/outreach",
            method="POST",
            parameters=[
                MCPToolParameter(name="place_id", type="string", description="Google Places ID", required=True),
                MCPToolParameter(name="name", type="string", description="Business name", required=True),
                MCPToolParameter(name="phone", type="string", description="Business phone number", required=True),
                MCPToolParameter(name="rating", type="number", description="Google rating", required=True),
                MCPToolParameter(name="review_count", type="integer", description="Number of reviews", required=True),
                MCPToolParameter(name="message", type="string", description="Custom message override", required=False),
            ],
            returns={"type": "object", "properties": {"status": {"type": "string"}, "preview_url": {"type": "string"}}},
        ),
        MCPTool(
            name="complianceone.get_status",
            description="Get compliance status across frameworks (SOC2, HIPAA, PCI-DSS, GDPR).",
            service="complianceone",
            endpoint="http://complianceone:8001/api/compliance/status",
            method="GET",
            parameters=[
                MCPToolParameter(name="framework", type="string", description="Specific framework or 'all'", required=False, default="all"),
            ],
            returns={"type": "object"},
        ),
        MCPTool(
            name="finops360.get_costs",
            description="Retrieve cloud cost analysis and right-sizing recommendations.",
            service="finops360",
            endpoint="http://finops360:8002/api/costs",
            method="GET",
            parameters=[
                MCPToolParameter(name="provider", type="string", description="Cloud provider: aws, azure, gcp, or all", required=False, default="all"),
                MCPToolParameter(name="days", type="integer", description="Number of days to analyze", required=False, default=30),
            ],
            returns={"type": "object"},
        ),
        MCPTool(
            name="orchestrator.scale_service",
            description="Scale a platform service up or down using the Orchestrator.",
            service="orchestrator",
            endpoint="http://orchestrator:9000/services/{name}/scale",
            method="POST",
            parameters=[
                MCPToolParameter(name="name", type="string", description="Service name: money, complianceone, finops360, growthengine", required=True, enum=["money", "complianceone", "finops360", "growthengine"]),
                MCPToolParameter(name="target_instances", type="integer", description="Desired instance count", required=True),
            ],
            returns={"type": "object", "properties": {"scaled_to": {"type": "integer"}, "status": {"type": "string"}}},
        ),
        MCPTool(
            name="orchestrator.get_health",
            description="Get platform-wide health status from the Orchestrator.",
            service="orchestrator",
            endpoint="http://orchestrator:9000/health",
            method="GET",
            parameters=[],
            returns={"type": "object"},
        ),
        MCPTool(
            name="event_bus.publish",
            description="Publish an event to the ReliantAI event bus for cross-service communication.",
            service="integration",
            endpoint="http://integration:8080/publish",
            method="POST",
            parameters=[
                MCPToolParameter(name="event_type", type="string", description="Event type in snake.dot.notation", required=True),
                MCPToolParameter(name="payload", type="object", description="Event payload object (max 64KB)", required=True),
                MCPToolParameter(name="correlation_id", type="string", description="Correlation ID for tracing", required=False),
            ],
            returns={"type": "object", "properties": {"event_id": {"type": "string"}}},
        ),
        MCPTool(
            name="reliant_os.run_code",
            description="Execute Python code safely in the Reliant JIT OS sandbox. Use for code modifications, data analysis, or system operations.",
            service="reliant-os",
            endpoint="http://reliant-os-backend:8004/api/os/chat",
            method="POST",
            parameters=[
                MCPToolParameter(name="message", type="string", description="Natural language request or code command", required=True),
                MCPToolParameter(name="mode", type="string", description="AI mode: auto, chat, code, sales", required=False, default="auto"),
            ],
            returns={"type": "object", "properties": {"reply": {"type": "string"}, "execution_results": {"type": "array"}}},
        ),
    ]
    
    for tool in built_ins:
        _tools[tool.name] = tool
    print(f"[MCP Bridge] Bootstrapped {len(built_ins)} built-in tools")

@app.on_event("startup")
async def startup():
    await _bootstrap_tools()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8083)

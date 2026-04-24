"""
ReliantAI JIT Operating System - Backend API
=============================================
Secure initialization, multi-role AI execution, and system management.
No .env files required - all configuration is UI-driven and stored securely.
"""

import os
import json
import subprocess
import sqlite3
import re
import hashlib
import secrets as _secrets
import time
import asyncio
from datetime import datetime
from typing import Optional

import httpx
import redis.asyncio as aioredis
import google.generativeai as genai
from fastapi import FastAPI, HTTPException, Request, Depends, Security
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

# ── MCP Bridge Integration ──────────────────────────────────────

_redis_pool: aioredis.Redis | None = None

async def _get_redis() -> aioredis.Redis:
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(REDIS_URL, decode_responses=True)
    return _redis_pool
MCP_BRIDGE_URL = os.environ.get("MCP_BRIDGE_URL", "http://mcp-bridge:8083")
MCP_API_KEY = os.environ.get("MCP_API_KEY", "")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")

# Cache MCP tools for 60s to avoid hammering the bridge
_mcp_tools_cache = None
_mcp_tools_cache_time = 0


def fetch_mcp_tools_sync() -> list[dict]:
    """Fetch available MCP tools from the bridge (synchronous, with caching)."""
    global _mcp_tools_cache, _mcp_tools_cache_time
    now = time.time()
    if _mcp_tools_cache is not None and (now - _mcp_tools_cache_time) < 60:
        return _mcp_tools_cache
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{MCP_BRIDGE_URL}/mcp/tools")
            if resp.status_code == 200:
                data = resp.json()
                tools = data if isinstance(data, list) else data.get("tools", [])
                _mcp_tools_cache = tools
                _mcp_tools_cache_time = now
                return tools
    except Exception:
        pass
    return []


def format_tools_for_prompt(tools: list[dict]) -> str:
    """Format tool definitions into a compact system prompt fragment."""
    if not tools:
        return ""
    lines = ["\n## Available Platform Tools\nYou may invoke any of the following tools by outputting a JSON block like:\n"]
    lines.append('```json\n{"tool": "service.tool_name", "parameters": {"key": "value"}}\n```\n')
    lines.append("Available tools:\n")
    for t in tools:
        name = t.get("name", "unknown")
        desc = t.get("description", "No description")
        params = t.get("parameters", {})
        param_str = ", ".join([f'{k} ({v.get("type","any")})' for k, v in params.items()]) if params else "none"
        lines.append(f'- {name}: {desc}. Parameters: {param_str}')
    lines.append("\nOnly output a tool call JSON block when the user explicitly asks for data or an action that matches a tool. Do not hallucinate tool names.")
    return "\n".join(lines)


def execute_mcp_tool_sync(tool_name: str, parameters: dict) -> dict:
    try:
        headers = {}
        if MCP_API_KEY:
            headers["X-API-Key"] = MCP_API_KEY
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                f"{MCP_BRIDGE_URL}/mcp/tools/call",
                json={"tool": tool_name, "parameters": parameters},
                headers=headers,
            )
            resp.raise_for_status()
            return resp.json()
    except Exception as e:
        return {"status": "error", "error": str(e)}


def parse_mcp_calls_from_reply(reply: str) -> list[dict]:
    """Parse JSON tool-call blocks from an AI reply. Validates tool names against known registry."""
    calls = []
    known_tools = {t.get("name") for t in fetch_mcp_tools_sync()} if _mcp_tools_cache else None
    json_blocks = re.findall(r'```json\n(.*?)\n```', reply, re.DOTALL)
    for block in json_blocks:
        try:
            obj = json.loads(block)
            if isinstance(obj, dict) and "tool" in obj:
                tool_name = obj["tool"]
                if known_tools is not None and tool_name not in known_tools:
                    continue
                if not isinstance(obj.get("parameters", {}), dict):
                    continue
                calls.append({
                    "tool": tool_name,
                    "parameters": obj.get("parameters", {})
                })
        except json.JSONDecodeError:
            continue
    return calls

app = FastAPI(title="Reliant JIT OS", version="2.0.0")

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

OS_API_KEY = os.environ.get("OS_API_KEY", "")
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_os_api_key(api_key: str = Security(_api_key_header)) -> str:
    if not OS_API_KEY:
        raise HTTPException(status_code=503, detail="OS API key not configured. Set OS_API_KEY environment variable.")
    if not api_key or not _secrets.compare_digest(api_key, OS_API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return api_key

DB_PATH = os.environ.get("SECURE_DATA_PATH", "/secure_data") + "/reliant_os.db"
EXECUTION_LOG_PATH = os.environ.get("SECURE_DATA_PATH", "/secure_data") + "/execution_log.db"
ALLOWED_PATHS = ["/workspace", "/tmp", "/secure_data"]
BLOCKED_COMMANDS = ["rm -rf /", "rm  -rf /", "mkfs", "dd if=/dev/zero", ":(){ :|:& };:", "shutdown", "reboot", "halt", "sudo rm"]
BLOCKED_IMPORTS = ["subprocess", "os.system", "os.popen", "__import__", "ctypes", "socket", "pickle", "importlib"]
BLOCKED_BUILTINS = ["eval", "exec", "compile", "__builtins__", "getattr", "setattr", "delattr"]
BLOCKED_FILE_READS = ["/etc/shadow", "/etc/passwd", "/proc/", "/sys/", "/root/.ssh", "/home/"]
MAX_EXECUTION_TIME = 30
SANDBOX_ENV = {
    key: value for key, value in os.environ.items()
    if key not in ("DATABASE_URL", "REDIS_URL", "GEMINI_API_KEY", "STRIPE_SECRET_KEY",
                    "TWILIO_SID", "TWILIO_TOKEN", "AUTH_SECRET_KEY", "JWT_SECRET",
                    "DISPATCH_API_KEY", "MCP_API_KEY", "OS_API_KEY", "HEAL_API_KEY",
                    "POSTGRES_PASSWORD", "REDIS_PASSWORD")
}


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=5000")
    c.execute('''CREATE TABLE IF NOT EXISTS secrets (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS execution_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        prompt TEXT,
        code_hash TEXT,
        result TEXT,
        status TEXT,
        execution_time_ms INTEGER
    )''')
    conn.commit()
    conn.close()


def get_secret(key):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT value FROM secrets WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None


def set_secret(key, value):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""INSERT OR REPLACE INTO secrets (key, value, updated_at)
        VALUES (?, ?, CURRENT_TIMESTAMP)""", (key, value))
    conn.commit()
    conn.close()


def log_execution(prompt, code, result, status, exec_time):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    code_hash = hashlib.sha256(code.encode()).hexdigest()[:16]
    c.execute("""INSERT INTO execution_log (prompt, code_hash, result, status, execution_time_ms)
        VALUES (?, ?, ?, ?, ?)""", (prompt, code_hash, result, status, exec_time))
    conn.commit()
    conn.close()


def validate_code_safety(code: str) -> tuple[bool, str]:
    for blocked in BLOCKED_COMMANDS:
        if blocked in code:
            return False, f"Blocked dangerous command detected: {blocked}"
    for blocked_import in BLOCKED_IMPORTS:
        base = blocked_import.split(".")[0]
        pattern = rf'(?:import\s+{re.escape(base)}|from\s+{re.escape(base)}\s+import)'
        if re.search(pattern, code) or re.search(rf'\b{re.escape(base)}\.', code):
            return False, f"Blocked import: {blocked_import}"
    for blocked_builtin in BLOCKED_BUILTINS:
        if re.search(rf'\b{re.escape(blocked_builtin)}\s*\(', code):
            return False, f"Blocked builtin: {blocked_builtin}"
        if blocked_builtin in code and blocked_builtin.startswith("__"):
            return False, f"Blocked builtin access: {blocked_builtin}"
    for blocked_path in BLOCKED_FILE_READS:
        if blocked_path in code:
            return False, f"Blocked file path access: {blocked_path}"
    if re.search(r'os\.remove\s*\(|os\.rmdir\s*\(|shutil\.rmtree\s*\(', code):
        if not any(safe in code for safe in ['/tmp/', '/workspace/', '/secure_data/']):
            return False, "File deletion only allowed in /tmp, /workspace, or /secure_data"
    if re.search(r'\benviron\b|\bgetenv\b|\bENVIRON\b', code):
        return False, "Environment variable access is restricted in sandbox"
    if re.search(r'\bopen\s*\(', code) and not re.search(r"open\s*\(\s*['\"](/tmp|/workspace|/secure_data)", code):
        return False, "File access restricted to /tmp, /workspace, /secure_data"
    return True, "Safe"


init_db()


class SetupRequest(BaseModel):
    gemini_key: str
    stripe_key: str
    twilio_sid: str
    twilio_token: str
    places_key: str


class ChatRequest(BaseModel):
    message: str
    history: list = []
    mode: str = "auto"  # auto, chat, code, sales


@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "reliant-os-backend", "version": "2.0.0"}


@app.get("/api/os/status")
def get_status():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    keys_to_check = ["GEMINI_API_KEY", "TWILIO_SID", "STRIPE_SECRET_KEY"]
    placeholders = ",".join("?" * len(keys_to_check))
    c.execute(f"SELECT key, value FROM secrets WHERE key IN ({placeholders})", keys_to_check)
    rows = c.fetchall()
    conn.close()
    found = {row[0]: bool(row[1]) for row in rows}
    configured = {k: found.get(k, False) for k in keys_to_check}
    missing = [k for k, v in configured.items() if not v]
    return {
        "configured": len(missing) == 0,
        "missing": missing,
        "services": configured,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/os/setup")
def setup_system(req: SetupRequest, _auth: str = Depends(verify_os_api_key)):
    set_secret("GEMINI_API_KEY", req.gemini_key)
    set_secret("STRIPE_SECRET_KEY", req.stripe_key)
    set_secret("TWILIO_SID", req.twilio_sid)
    set_secret("TWILIO_TOKEN", req.twilio_token)
    set_secret("GOOGLE_PLACES_API_KEY", req.places_key)
    
    # Restart the stack to pick up new credentials
    subprocess.Popen(
        ["sh", "-c", "cd /workspace && docker compose up -d"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    return {
        "status": "success",
        "message": "System configured and restarting. All services will be available shortly."
    }


@app.post("/api/os/chat")
def chat_jit(req: ChatRequest, _auth: str = Depends(verify_os_api_key)):
    api_key = get_secret("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="Gemini API Key not set. Please run setup first.")
    
    genai.configure(api_key=api_key)
    
    # Select model based on mode
    model_name = 'gemini-2.5-flash' if req.mode != 'code' else 'gemini-2.5-pro'
    model = genai.GenerativeModel(model_name)
    
    # Fetch available MCP tools and inject into prompt
    mcp_tools = fetch_mcp_tools_sync()
    tools_fragment = format_tools_for_prompt(mcp_tools)

    # Role-specific system prompts
    system_prompts = {
        "auto": f"""You are the ReliantAI JIT Operating System. You have direct read/write access to the entire codebase mounted at /workspace.
If the user asks you to modify code, add a feature, or fix a bug, output ONLY valid Python code inside ```python ... ``` blocks.
The code will be executed directly. You can use os, subprocess, file I/O, etc.
If the user asks a question, answer it directly.
Always wrap executable code in ```python ... ```.{tools_fragment}""",
        
        "chat": f"""You are the ReliantAI Support Agent. Answer questions about the system, help users understand features, and provide guidance.
Be friendly, concise, and helpful. You do not execute code unless explicitly requested.{tools_fragment}""",
        
        "sales": f"""You are the ReliantAI Sales Representative. Help potential customers understand the value of our platform.
Highlight features like autonomous lead generation, AI-powered dispatch, compliance automation, and revenue optimization.
Be persuasive but honest. Guide users toward scheduling a demo or signing up.{tools_fragment}""",
        
        "code": f"""You are the ReliantAI Senior Engineer. Write production-quality Python code.
Follow PEP 8, add type hints, include error handling, and write clean, maintainable code.
Always wrap code in ```python ... ``` blocks.{tools_fragment}"""
    }
    
    prompt = system_prompts.get(req.mode, system_prompts["auto"])
    full_prompt = f"{prompt}\n\nUser Message: {req.message}"
    
    try:
        start_time = time.time()
        response = model.generate_content(full_prompt)
        reply = response.text
        exec_time = int((time.time() - start_time) * 1000)

        # ── Auto-execute MCP tool calls ───────────────────────────
        mcp_results = []
        mcp_calls = parse_mcp_calls_from_reply(reply)
        if mcp_calls:
            for call in mcp_calls:
                tool_start = time.time()
                tool_result = execute_mcp_tool_sync(call["tool"], call["parameters"])
                tool_duration = int((time.time() - tool_start) * 1000)
                mcp_results.append({
                    "tool": call["tool"],
                    "parameters": call["parameters"],
                    "result": tool_result,
                    "execution_time_ms": tool_duration
                })
                log_execution(req.message, json.dumps(call), json.dumps(tool_result),
                              "mcp_success" if tool_result.get("status") != "error" else "mcp_error",
                              tool_duration)

        # Check for executable code blocks
        execution_results = []
        if "```python" in reply:
            code_blocks = re.findall(r'```python\n(.*?)\n```', reply, re.DOTALL)
            
            for code_block in code_blocks:
                # Safety validation
                is_safe, reason = validate_code_safety(code_block)
                if not is_safe:
                    execution_results.append(f"[BLOCKED] {reason}")
                    log_execution(req.message, code_block, reason, "blocked", 0)
                    continue
                
                # Execute with timeout
                with open("/tmp/jit_exec.py", "w") as f:
                    f.write(code_block)
                
                try:
                    exec_start = time.time()
                    result = subprocess.run(
                        ["python3", "/tmp/jit_exec.py"],
                        capture_output=True,
                        text=True,
                        cwd="/workspace",
                        timeout=MAX_EXECUTION_TIME,
                        env=SANDBOX_ENV,
                    )
                    exec_duration = int((time.time() - exec_start) * 1000)
                    output = result.stdout + result.stderr
                    
                    if result.returncode != 0:
                        execution_results.append(f"[ERROR] {output}")
                        log_execution(req.message, code_block, output, "error", exec_duration)
                    else:
                        execution_results.append(output)
                        log_execution(req.message, code_block, output, "success", exec_duration)
                        
                except subprocess.TimeoutExpired:
                    execution_results.append(f"[TIMEOUT] Execution exceeded {MAX_EXECUTION_TIME} seconds")
                    log_execution(req.message, code_block, "timeout", "timeout", MAX_EXECUTION_TIME * 1000)
                except Exception as e:
                    execution_results.append(f"[ERROR] {str(e)}")
                    log_execution(req.message, code_block, str(e), "error", 0)
        
        return {
            "reply": reply,
            "execution_results": execution_results if execution_results else None,
            "mcp_results": mcp_results if mcp_results else None,
            "mode": req.mode,
            "execution_time_ms": exec_time
        }
        
    except Exception as e:
        return {
            "reply": f"Error calling Gemini: {str(e)}",
            "execution_results": None,
            "mcp_results": None,
            "mode": req.mode,
            "execution_time_ms": 0
        }


# ── MCP (Model Context Protocol) Endpoints ────────────────────────
# These allow the AI to discover and call tools across all platform services

@app.get("/api/os/mcp/tools")
async def mcp_list_tools(service: Optional[str] = None, capability: Optional[str] = None, _auth: str = Depends(verify_os_api_key)):
    try:
        headers = {}
        if MCP_API_KEY:
            headers["X-API-Key"] = MCP_API_KEY
        async with httpx.AsyncClient() as client:
            params = {}
            if service:
                params["service"] = service
            if capability:
                params["capability"] = capability
            response = await client.get(f"{MCP_BRIDGE_URL}/mcp/tools", params=params, timeout=10.0, headers=headers)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e), "bridge_available": False}

@app.post("/api/os/mcp/call")
async def mcp_call_tool(request: Request, _auth: str = Depends(verify_os_api_key)):
    try:
        body = await request.json()
        headers = {}
        if MCP_API_KEY:
            headers["X-API-Key"] = MCP_API_KEY
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MCP_BRIDGE_URL}/mcp/tools/call",
                json=body,
                timeout=30.0,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/api/os/mcp/history")
async def mcp_tool_history(limit: int = 50, _auth: str = Depends(verify_os_api_key)):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MCP_BRIDGE_URL}/mcp/tools/history", params={"limit": limit}, timeout=10.0)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/os/health")
async def platform_health():
    """Get aggregated platform health from the health aggregator."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://health-aggregator:8086/health/aggregate", timeout=10.0)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e), "aggregator_available": False}

# ── Real-Time Event Stream (SSE) ──────────────────────────────

@app.get("/api/os/events/stream")
async def event_stream(request: Request, _auth: str = Depends(verify_os_api_key)):
    
    client_ip = request.client.host if request.client else "unknown"
    
    async def generate():
        pubsub = None
        try:
            r = await _get_redis()
            pubsub = r.pubsub()
            await pubsub.subscribe("events:health", "events:mcp:tool_call")
            
            yield f"data: {json.dumps({'event': 'connected', 'channels': ['events:health', 'events:mcp:tool_call']})}\n\n"
            
            heartbeat_count = 0
            async for message in pubsub.listen():
                if await request.is_disconnected():
                    break
                if message["type"] == "message":
                    heartbeat_count = 0
                    try:
                        data = message["data"]
                        if isinstance(data, bytes):
                            data = data.decode("utf-8", errors="replace")
                        payload = json.loads(data)
                        payload["channel"] = message["channel"].decode() if isinstance(message["channel"], bytes) else message["channel"]
                        yield f"data: {json.dumps(payload)}\n\n"
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        yield f"data: {json.dumps({'event': 'raw', 'data': str(message['data'])[:200]})}\n\n"
                elif message["type"] == "heartbeat":
                    heartbeat_count += 1
                    if heartbeat_count % 4 == 0:
                        yield ": keepalive\n\n"
                        
        except asyncio.CancelledError:
            raise
        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'error': str(e)})}\n\n"
        finally:
            if pubsub:
                try:
                    await pubsub.unsubscribe()
                    await pubsub.aclose()
                except Exception:
                    pass
    
    return StreamingResponse(generate(), media_type="text/event-stream")

# ── Execution History ───────────────────────────────────────────

@app.get("/api/os/execution-history")
def get_execution_history(limit: int = 50, _auth: str = Depends(verify_os_api_key)):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""SELECT timestamp, prompt, code_hash, status, execution_time_ms
        FROM execution_log ORDER BY timestamp DESC LIMIT ?""", (limit,))
    rows = c.fetchall()
    conn.close()
    
    return {
        "history": [
            {
                "timestamp": row[0],
                "prompt": row[1],
                "code_hash": row[2],
                "status": row[3],
                "execution_time_ms": row[4]
            }
            for row in rows
        ]
    }

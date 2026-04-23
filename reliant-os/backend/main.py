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
import time
from datetime import datetime
from typing import Optional

import httpx
import google.generativeai as genai
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware

# ── MCP Bridge Integration ──────────────────────────────────────
MCP_BRIDGE_URL = os.environ.get("MCP_BRIDGE_URL", "http://mcp-bridge:8083")

app = FastAPI(title="Reliant JIT OS", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = os.environ.get("SECURE_DATA_PATH", "/secure_data") + "/reliant_os.db"
EXECUTION_LOG_PATH = os.environ.get("SECURE_DATA_PATH", "/secure_data") + "/execution_log.db"
ALLOWED_PATHS = ["/workspace", "/tmp", "/secure_data"]
BLOCKED_COMMANDS = ["rm -rf /", "mkfs", "dd if=/dev/zero", ":(){ :|:& };:", "shutdown", "reboot", "halt"]
MAX_EXECUTION_TIME = 30  # seconds


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
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
    """Validate that generated code is safe to execute."""
    # Check for blocked commands in shell executions
    for blocked in BLOCKED_COMMANDS:
        if blocked in code:
            return False, f"Blocked dangerous command detected: {blocked}"
    
    # Check for unrestricted file deletion
    if re.search(r'os\.remove\s*\(|os\.rmdir\s*\(|shutil\.rmtree\s*\(', code):
        if not any(safe in code for safe in ['/tmp/', '/workspace/', '/secure_data/']):
            return False, "File deletion only allowed in /tmp, /workspace, or /secure_data"
    
    # Check for network access restrictions (optional - can be enabled)
    # if 'socket' in code and 'import socket' in code:
    #     return False, "Raw socket access is restricted"
    
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
    keys_to_check = ["GEMINI_API_KEY", "TWILIO_SID", "STRIPE_SECRET_KEY"]
    configured = {k: bool(get_secret(k)) for k in keys_to_check}
    missing = [k for k, v in configured.items() if not v]
    return {
        "configured": len(missing) == 0,
        "missing": missing,
        "services": configured,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/api/os/setup")
def setup_system(req: SetupRequest):
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
def chat_jit(req: ChatRequest):
    api_key = get_secret("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="Gemini API Key not set. Please run setup first.")
    
    genai.configure(api_key=api_key)
    
    # Select model based on mode
    model_name = 'gemini-2.5-flash' if req.mode != 'code' else 'gemini-2.5-pro'
    model = genai.GenerativeModel(model_name)
    
    # Role-specific system prompts
    system_prompts = {
        "auto": """You are the ReliantAI JIT Operating System. You have direct read/write access to the entire codebase mounted at /workspace.
If the user asks you to modify code, add a feature, or fix a bug, output ONLY valid Python code inside ```python ... ``` blocks.
The code will be executed directly. You can use os, subprocess, file I/O, etc.
If the user asks a question, answer it directly.
Always wrap executable code in ```python ... ```.""",
        
        "chat": """You are the ReliantAI Support Agent. Answer questions about the system, help users understand features, and provide guidance.
Be friendly, concise, and helpful. You do not execute code unless explicitly requested.""",
        
        "sales": """You are the ReliantAI Sales Representative. Help potential customers understand the value of our platform.
Highlight features like autonomous lead generation, AI-powered dispatch, compliance automation, and revenue optimization.
Be persuasive but honest. Guide users toward scheduling a demo or signing up.""",
        
        "code": """You are the ReliantAI Senior Engineer. Write production-quality Python code.
Follow PEP 8, add type hints, include error handling, and write clean, maintainable code.
Always wrap code in ```python ... ``` blocks."""
    }
    
    prompt = system_prompts.get(req.mode, system_prompts["auto"])
    full_prompt = f"{prompt}\n\nUser Message: {req.message}"
    
    try:
        start_time = time.time()
        response = model.generate_content(full_prompt)
        reply = response.text
        exec_time = int((time.time() - start_time) * 1000)
        
        # Check for executable code blocks
        if "```python" in reply:
            code_blocks = re.findall(r'```python\n(.*?)\n```', reply, re.DOTALL)
            
            execution_results = []
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
                        timeout=MAX_EXECUTION_TIME
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
                "execution_results": execution_results,
                "mode": req.mode,
                "execution_time_ms": exec_time
            }
        
        return {
            "reply": reply,
            "execution_results": None,
            "mode": req.mode,
            "execution_time_ms": exec_time
        }
        
    except Exception as e:
        return {
            "reply": f"Error calling Gemini: {str(e)}",
            "execution_results": None,
            "mode": req.mode,
            "execution_time_ms": 0
        }


# ── MCP (Model Context Protocol) Endpoints ────────────────────────
# These allow the AI to discover and call tools across all platform services

@app.get("/api/os/mcp/tools")
async def mcp_list_tools(service: Optional[str] = None, capability: Optional[str] = None):
    """Discover available MCP tools across the platform."""
    try:
        async with httpx.AsyncClient() as client:
            params = {}
            if service:
                params["service"] = service
            if capability:
                params["capability"] = capability
            response = await client.get(f"{MCP_BRIDGE_URL}/mcp/tools", params=params, timeout=10.0)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"error": str(e), "bridge_available": False}

@app.post("/api/os/mcp/call")
async def mcp_call_tool(request: Request):
    """Execute an MCP tool call on behalf of the AI."""
    try:
        body = await request.json()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MCP_BRIDGE_URL}/mcp/tools/call",
                json=body,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/api/os/mcp/history")
async def mcp_tool_history(limit: int = 50):
    """Get MCP tool execution history."""
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

# ── Execution History ───────────────────────────────────────────

@app.get("/api/os/execution-history")
def get_execution_history(limit: int = 50):
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

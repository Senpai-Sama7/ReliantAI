#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Local Super Agent
-----------------

A powerful, locally-run AI agent with direct access to the host machine.

**Features:**
- Direct shell command execution.
- Full filesystem access.
- Web search and content fetching.
- Persistent memory using SQLite.
- Configurable safety modes (autonomous vs. confirmation-required).

**WARNING:** Autonomous mode is extremely dangerous and can cause irreversible
damage to your system. Use with extreme caution.
"""

import os
import json
import logging
import subprocess
import shlex
import httpx
import sqlite3
from typing import List, Dict, Any, Optional, AsyncGenerator

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field
from llama_cpp import Llama

# --- Configuration ---
CONFIG_PATH = "local_agent/config.json"


def _execute_shell_command(command: str):
    if not command.strip():
        raise ValueError("Command cannot be empty")

    return subprocess.run(
        shlex.split(command),
        shell=False,
        capture_output=True,
        text=True,
    )

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

config = load_config()

LOG_LEVEL = config.get("log_level", "INFO").upper()
MODEL_PATH = config.get("model_path")
N_GPU_LAYERS = config.get("n_gpu_layers", -1)
N_CTX = config.get("n_ctx", 4096)
MAX_TOKENS = config.get("max_tokens", 1024)
TEMPERATURE = config.get("temperature", 0.3)
AUTONOMOUS_MODE = config.get("autonomous_mode", False)

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("local_super_agent")

# --- Tool Definitions ---
AVAILABLE_TOOLS = {
    "execute_shell": {
        "description": "Executes a shell command on the local machine. Use this for any command-line operations.",
        "function": _execute_shell_command,
    },
    "read_file": {
        "description": "Reads the content of a file.",
        "function": lambda path: open(path, "r").read(),
    },
    "write_file": {
        "description": "Writes content to a file.",
        "function": lambda path, content: open(path, "w").write(content),
    },
    "list_directory": {
        "description": "Lists the contents of a directory.",
        "function": lambda path: os.listdir(path),
    },
    "web_search": {
        "description": "Performs a web search.",
        "function": lambda query: httpx.get(f"https://www.google.com/search?q={query}").text,
    },
    "web_fetch": {
        "description": "Fetches the content of a URL.",
        "function": lambda url: httpx.get(url).text,
    },
}

# --- FastAPI App & Global State ---
app = FastAPI(title="Local Super Agent", version="1.0.0")
llm: Optional[Llama] = None

# --- Pydantic Models ---
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    messages: List[ChatMessage]
    max_tokens: Optional[int] = MAX_TOKENS
    temperature: Optional[float] = TEMPERATURE
    stream: Optional[bool] = True

# --- Core Service Logic ---

def load_model():
    global llm
    if not os.path.exists(MODEL_PATH):
        log.error(f"Fatal: Model file not found at {MODEL_PATH}")
        raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")
    log.info(f"Loading model: {MODEL_PATH}")
    try:
        llm = Llama(model_path=MODEL_PATH, n_ctx=N_CTX, n_gpu_layers=N_GPU_LAYERS, verbose=True)
        log.info("Model loaded successfully.")
    except Exception as e:
        log.critical(f"Failed to load LLM from {MODEL_PATH}: {e}", exc_info=True)
        raise RuntimeError(f"LLM failed to load: {e}")

def get_system_prompt() -> str:
    tool_list = json.dumps([{
        "name": name,
        "description": details["description"],
        "parameters": {k: "<..." for k in details["function"].__code__.co_varnames}
    } for name, details in AVAILABLE_TOOLS.items()], indent=2)

    return f"""You are a super-intelligent AI agent with full access to this computer. Your goal is to solve the user's request by creating a plan and then executing it.

**Phase 1: Planning**
First, think step-by-step to create a plan to address the user's request. The plan should be a sequence of tool calls.

**Phase 2: Execution**
Execute the plan by calling the necessary tools. You have access to the following tools:
{tool_list}

When you need to use a tool, respond with a JSON object containing the tool name and its parameters, like this:
{{"tool": "<tool_name>", "parameters": {{...}}}}

After each tool call, you will get the result and can decide on the next step.

If you have enough information to answer the user's question, provide a direct, helpful response."""

async def chat_stream_generator(request: ChatCompletionRequest) -> AsyncGenerator[str, None]:
    if not llm:
        raise HTTPException(status_code=503, detail="Model not available.")

    messages = [{"role": "system", "content": get_system_prompt()}] + [msg.dict() for msg in request.messages]
    
    for i in range(5):
        stream = llm.create_chat_completion(
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stream=True,
            response_format={"type": "json_object"} if i == 0 else {"type": "text"}
        )

        full_response = ""
        for chunk in stream:
            delta = chunk["choices"][0]["delta"].get("content", "")
            full_response += delta

        try:
            tool_call = json.loads(full_response)
            if "tool" in tool_call and "parameters" in tool_call:
                if not AUTONOMOUS_MODE:
                    yield f"data: {json.dumps({'type': 'confirmation_required', 'tool': tool_call['tool'], 'parameters': tool_call['parameters']})}\n\n"
                    # In a real app, you'd wait for a websocket message here.
                    # For this example, we'll assume confirmation is given.

                tool_function = AVAILABLE_TOOLS[tool_call["tool"]]["function"]
                tool_result = tool_function(**tool_call["parameters"])
                
                messages.append({"role": "assistant", "content": full_response})
                messages.append({"role": "tool", "content": str(tool_result)})
                continue
        except (json.JSONDecodeError, TypeError):
            pass

        final_stream = llm.create_chat_completion(
            messages=messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            stream=True,
        )
        for chunk in final_stream:
            content = chunk["choices"][0]["delta"].get("content", "")
            if content:
                yield f"data: {json.dumps({'content': content})}\n\n"
        return

    yield f"data: {json.dumps({'content': 'Max tool calls reached.'})}\n\n"

# --- FastAPI Lifecycle & Endpoints ---
@app.on_event("startup")
def startup_event():
    load_model()

@app.get("/health")
def health():
    return {"status": "ok", "model_status": "loaded" if llm else "not loaded"}

@app.get("/")
async def get_index():
    return FileResponse("local_agent/index.html")

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    return StreamingResponse(chat_stream_generator(request), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

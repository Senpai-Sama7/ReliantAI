#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Local Super Agent - Core Logic (Refactored)
-------------------------------------------

This module contains the core AI logic for the Local Super Agent, including
LLM interaction, tool definitions, and the main chat processing loop. It has
been refactored for enterprise-readiness with centralized configuration,
improved security, and robust error handling.
"""

import asyncio
import os
import json
import logging
import subprocess
import shlex
import sqlite3
import re
from typing import List, Dict, Any, Optional, Callable, Coroutine

import httpx
from llama_cpp import Llama
from git import Repo, InvalidGitRepositoryError

# --- Enterprise Configuration ---
# All configurations are loaded from environment variables for security and flexibility.
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
MODEL_PATH = os.getenv("MODEL_PATH")
N_GPU_LAYERS = int(os.getenv("N_GPU_LAYERS", -1))
N_CTX = int(os.getenv("N_CTX", 4096))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 1024))
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.3))
AUTONOMOUS_MODE = os.getenv("AUTONOMOUS_MODE", "false").lower() == "true"
GATEWAY_URL = os.getenv("GATEWAY_URL")
API_KEY = os.getenv("API_KEY")

# --- Logging Setup ---
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
log = logging.getLogger("local_super_agent_core")

# --- Pre-flight Checks ---
if not MODEL_PATH or not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"MODEL_PATH environment variable is not set or model file does not exist at '{MODEL_PATH}'")
if not GATEWAY_URL:
    raise ValueError("GATEWAY_URL environment variable is not set.")
if not API_KEY:
    raise ValueError("API_KEY environment variable is not set.")


# --- Persistent Memory (SQLite) ---
DB_PATH = "local_agent/memory.db"

def init_db():
    """Initializes the SQLite database for persistent memory."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                fact TEXT NOT NULL
            )
        ''')
        conn.commit()
    except sqlite3.Error as e:
        log.error(f"Database initialization error: {e}", exc_info=True)
    finally:
        if conn:
            conn.close()

init_db()

# --- Tool Definitions ---
class Tool:
    """A class to represent a tool that the agent can use."""
    def __init__(self, name: str, description: str, func: Callable, requires_confirmation: bool = False):
        self.name = name
        self.description = description
        self.func = func
        self.requires_confirmation = requires_confirmation
        self.parameters = {k: "<...>" for k in func.__code__.co_varnames if k != 'self'}

    def to_dict(self):
        """Returns a dictionary representation of the tool."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }

def _run_shell_command(command: str) -> str:
    """Executes a shell command securely and returns the output."""
    if not command:
        return "ERROR: Empty command provided."
    try:
        log.info(f"Executing shell command: {command}")
        result = subprocess.run(
            shlex.split(command),
            shell=False,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
        output = f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}\nExit Code: {result.returncode}"
        return output
    except subprocess.TimeoutExpired:
        return "ERROR: Command timed out after 120 seconds."
    except Exception as e:
        log.error(f"Error executing shell command: {e}", exc_info=True)
        return f"ERROR: An unexpected error occurred: {str(e)}"

def _read_file(path: str) -> str:
    """Reads the content of a file."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return f"ERROR: File not found at {path}"
    except Exception as e:
        return f"ERROR: Could not read file: {str(e)}"

def _write_file(path: str, content: str) -> str:
    """Writes content to a file."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"ERROR: Could not write to file: {str(e)}"

def _list_directory(path: str) -> str:
    """Lists the contents of a directory."""
    try:
        return "\n".join(os.listdir(path))
    except FileNotFoundError:
        return f"ERROR: Directory not found at {path}"
    except Exception as e:
        return f"ERROR: Could not list directory: {str(e)}"

def _save_memory(fact: str) -> str:
    """Saves a fact to the agent's persistent memory."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO memory (fact) VALUES (?)", (fact,))
        conn.commit()
        return "Fact saved to memory."
    except sqlite3.Error as e:
        return f"ERROR: Could not save fact to memory: {e}"
    finally:
        if conn:
            conn.close()

def _retrieve_memory(query: str) -> str:
    """Retrieves facts from the agent's persistent memory."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT fact FROM memory WHERE fact LIKE ? ORDER BY timestamp DESC", (f"%{query}%",))
        results = cursor.fetchall()
        return "\n".join([row[0] for row in results]) if results else "No relevant facts found in memory."
    except sqlite3.Error as e:
        return f"ERROR: Could not retrieve facts from memory: {e}"
    finally:
        if conn:
            conn.close()

def _restart_agent() -> str:
    """Signals that the agent needs to be restarted."""
    return "RESTART_SIGNAL: Agent has modified its own code. Please restart the application to apply changes."

async def _call_remote_service(service: str, endpoint: str, payload: Dict[str, Any]) -> str:
    """Helper function to call a remote microservice via the API Gateway."""
    url = f"{GATEWAY_URL}/{service}/{endpoint}"
    headers = {"X-API-KEY": API_KEY, "Content-Type": "application/json"}
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers, timeout=120.0)
            response.raise_for_status()
            return json.dumps(response.json())
    except httpx.RequestError as e:
        return f"ERROR: Network error calling {service}/{endpoint}: {e}"
    except httpx.HTTPStatusError as e:
        return f"ERROR: Service {service}/{endpoint} returned HTTP error {e.response.status_code}: {e.response.text}"
    except Exception as e:
        return f"ERROR: Unexpected error calling {service}/{endpoint}: {e}"

async def _web_search(query: str) -> str:
    return await _call_remote_service("web", "search", {"query": query})

async def _web_fetch(url: str) -> str:
    return await _call_remote_service("web", "fetch", {"url": url})

async def _vector_search(query: str) -> str:
    return await _call_remote_service("vector", "search", {"query": query})

# --- Tool Registration ---
AVAILABLE_TOOLS = [
    Tool("execute_shell", "Executes a shell command.", _run_shell_command, requires_confirmation=True),
    Tool("read_file", "Reads a file from the filesystem.", _read_file),
    Tool("write_file", "Writes content to a file.", _write_file, requires_confirmation=True),
    Tool("list_directory", "Lists contents of a directory.", _list_directory),
    Tool("save_memory", "Saves a fact to persistent memory.", _save_memory),
    Tool("retrieve_memory", "Retrieves facts from persistent memory.", _retrieve_memory),
    Tool("web_search", "Performs a web search.", _web_search),
    Tool("web_fetch", "Fetches content from a URL.", _web_fetch),
    Tool("vector_search", "Performs a semantic vector search.", _vector_search),
    Tool("restart_agent", "Signals the agent to restart.", _restart_agent, requires_confirmation=True),
]

# --- LLM Agent Core ---
class Agent:
    def __init__(self):
        self.llm: Optional[Llama] = None
        self._load_model()
        self.tool_map = {tool.name: tool for tool in AVAILABLE_TOOLS}

    def _load_model(self):
        """Loads the Llama model from the configured path."""
        log.info(f"Loading model from: {MODEL_PATH}")
        try:
            self.llm = Llama(model_path=MODEL_PATH, n_ctx=N_CTX, n_gpu_layers=N_GPU_LAYERS, verbose=False)
            log.info("Model loaded successfully.")
        except Exception as e:
            log.critical(f"Failed to load LLM from {MODEL_PATH}: {e}", exc_info=True)
            raise RuntimeError(f"LLM failed to load: {e}")

    def get_system_prompt(self) -> str:
        """Generates the system prompt for the agent, including available tools."""
        tool_list_str = json.dumps([tool.to_dict() for tool in AVAILABLE_TOOLS], indent=2)
        return f"""You are a powerful, autonomous AI agent with access to this computer and the internet. Your goal is to solve the user's request by creating a plan and executing it using the tools available to you.

**Phase 1: Planning**
Analyze the user's request and create a step-by-step plan. Break down complex tasks into smaller, manageable steps.

**Phase 2: Execution**
Execute your plan by calling the necessary tools. You have access to these tools:
{tool_list_str}

To use a tool, respond with a JSON object:
{{"tool": "<tool_name>", "parameters": {{"arg1": "value1", ...}}}}

After each tool call, you will receive the result. Use it to inform your next action. If a tool requires confirmation, you must wait for user approval.

**Important:**
- Be cautious with `execute_shell` and `write_file`.
- If you modify your own code, you MUST use the `restart_agent` tool to apply changes.
- When you have completed the request, provide a clear, final answer to the user.
"""

    async def process_chat(
        self,
        messages: List[Dict[str, Any]],
        send_response: Callable[[str], Coroutine[Any, Any, None]],
        send_confirmation_request: Callable[[str, Dict[str, Any]], Coroutine[Any, Any, bool]]
    ) -> None:
        """Processes a chat message, handling the tool-use loop."""
        full_messages = [{"role": "system", "content": self.get_system_prompt()}] + messages

        for _ in range(10):  # Limit iterations to prevent infinite loops
            try:
                response = self.llm.create_chat_completion(
                    messages=full_messages,
                    max_tokens=MAX_TOKENS,
                    temperature=TEMPERATURE,
                    response_format={"type": "json_object"},
                )
                response_text = response['choices'][0]['message']['content'].strip()
                log.debug(f"LLM Raw Response: {response_text}")

                tool_call = json.loads(response_text)
                if "tool" in tool_call and "parameters" in tool_call:
                    tool_name = tool_call["tool"]
                    parameters = tool_call["parameters"]
                    log.info(f"LLM requested tool call: {tool_name} with {parameters}")

                    if tool_name not in self.tool_map:
                        tool_result = f"ERROR: Tool '{tool_name}' not found."
                    else:
                        tool_obj = self.tool_map[tool_name]
                        if tool_obj.requires_confirmation and not AUTONOMOUS_MODE:
                            if not await send_confirmation_request(tool_name, parameters):
                                tool_result = f"User denied execution of {tool_name}."
                            else:
                                if asyncio.iscoroutinefunction(tool_obj.func):
                                    tool_result = await tool_obj.func(**parameters)
                                else:
                                    tool_result = tool_obj.func(**parameters)
                        else:
                            if asyncio.iscoroutinefunction(tool_obj.func):
                                tool_result = await tool_obj.func(**parameters)
                            else:
                                tool_result = tool_obj.func(**parameters)

                    full_messages.append({"role": "assistant", "content": response_text})
                    full_messages.append({"role": "tool", "content": str(tool_result)})
                    continue
                else: # If the JSON does not contain a tool call, assume it's the final answer.
                    await send_response(tool_call.get("response", "Processing complete."))
                    return

            except (json.JSONDecodeError, TypeError):
                # The response was not valid JSON, so treat it as a direct answer.
                await send_response(response_text)
                return
            except Exception as e:
                log.error(f"Error during LLM interaction or tool loop: {e}", exc_info=True)
                await send_response(f"An error occurred: {e}")
                return

        await send_response("Max iterations reached. Please clarify your request.")

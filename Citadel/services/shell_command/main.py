#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Shell Command Service (Refactored)
----------------------------------

This service provides a secure endpoint for executing shell commands.
It is protected by API key authentication.
"""

import os
import logging
import subprocess
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

# --- Configuration ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
API_KEY = os.getenv("API_KEY")

# --- Command Allowlist ---
# Map logical command names to the actual shell commands to run.
# You can expand this list as needed.
ALLOWED_COMMANDS = {
    "list_files": ["ls", "-l"],
    "disk_usage": ["df", "-h"],
    "uptime": ["uptime"],
}

# --- Logging ---
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# --- Pre-flight Checks ---
if not API_KEY:
    raise ValueError("API_KEY environment variable is not set.")

# --- Models ---
class ShellCommand(BaseModel):
    command: str  # logical command name, not raw shell command

# --- Service Initialization ---
app = FastAPI(
    title="Shell Command Service",
    description="Executes shell commands.",
    version="2.0.0"
)

# --- Security ---
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

async def get_api_key(key: str = Security(api_key_header)):
    if key == API_KEY:
        return key
    else:
        raise HTTPException(status_code=403, detail="Invalid API Key")

# --- API Endpoints ---
@app.post("/execute", summary="Execute a shell command")
def execute_shell_command(cmd: ShellCommand, api_key: str = Security(get_api_key)):
    """
    Executes an allowed shell command specified by logical name and returns the output.
    """
    # Check if the requested command is allowed
    command_to_run = ALLOWED_COMMANDS.get(cmd.command)
    if not command_to_run:
        raise HTTPException(status_code=400, detail=f"Command '{cmd.command}' not allowed.")
    try:
        result = subprocess.run(
            command_to_run, shell=False, capture_output=True, text=True, check=True, timeout=120
        )
        return {"stdout": result.stdout, "stderr": result.stderr}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=400, detail={"stdout": e.stdout, "stderr": e.stderr})
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Command timed out after 120 seconds.")
    except Exception as e:
        logger.error(f"Error executing shell command: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {e}")

@app.get("/health", summary="Health check endpoint")
def health():
    """Provides a basic health check of the service."""
    return {"status": "ok"}

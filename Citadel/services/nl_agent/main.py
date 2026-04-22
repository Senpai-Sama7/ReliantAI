"""
Gemini-backed Natural Language Agent Service (FastAPI)
------------------------------------------------------

This service exposes an OpenAI-style `/v1/chat/completions` endpoint while
using Google's Gemini models as the backend planner and answer generator.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, AsyncIterator, Dict, List, Literal, Optional

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

# --- Configuration & Logging ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://api_gateway:8000")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 1024))
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.3))
SHELL_CONFIRMATION_REQUIRED = (
    os.getenv("SHELL_CONFIRMATION_REQUIRED", "true").lower() == "true"
)
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("nl_agent_service")

# --- Tool Definitions ---
AVAILABLE_TOOLS = {
    "web_search": {
        "description": "Performs a web search to find information on the internet. Use this when you need to find current events, facts, or general knowledge that might not be in the model's training data.",
        "endpoint": "/web/search",
        "payload": {"query": "<search_query>", "max_results": 5},
    },
    "web_fetch": {
        "description": "Fetches the content of a specific URL. Use this when you have a URL and need to read the content of that webpage.",
        "endpoint": "/web/fetch",
        "payload": {"url": "<url_to_fetch>"},
    },
    "vector_search": {
        "description": "Searches for information in a vector database. Use this for questions about general knowledge, documents, or to find similar items.",
        "endpoint": "/vector/search",
        "payload": {"query": "<user_query>", "top_k": 3},
    },
    "knowledge_graph": {
        "description": "Queries a graph database to find relationships between entities. Use this to answer questions about how things are connected.",
        "endpoint": "/graph/query",
        "payload": {"query": "<cypher_query>"},
    },
    "time_series_forecast": {
        "description": "Predicts future values for a time series. Use this for forecasting questions.",
        "endpoint": "/timeseries/forecast",
        "payload": {"series": [], "steps": 10},
    },
    "execute_shell": {
        "description": "Executes a shell command on the local machine. Use this to run commands, scripts, or interact with the filesystem.",
        "endpoint": "/shell/execute",
        "payload": {"command": "<command_to_execute>"},
    },
}

TOOL_DECISION_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "action": {"type": "string", "enum": ["tool", "answer"]},
        "tool": {"type": "string"},
        "parameters": {"type": "object", "additionalProperties": True},
        "answer": {"type": "string"},
    },
    "required": ["action"],
    "additionalProperties": False,
}

API_KEY = os.getenv("API_KEY", "")


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None
    messages: List[ChatMessage]
    max_tokens: Optional[int] = Field(default=MAX_TOKENS)
    temperature: Optional[float] = Field(default=TEMPERATURE)
    stream: bool = True


class ToolDecision(BaseModel):
    action: Literal["tool", "answer"]
    tool: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    answer: Optional[str] = None


def _gemini_api_key() -> str:
    return os.getenv("GEMINI_API_KEY", "")


def _selected_model(request_model: Optional[str]) -> str:
    return request_model or os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)


@asynccontextmanager
async def _get_async_client() -> AsyncIterator[Any]:
    api_key = _gemini_api_key()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set.")
    async with genai.Client(api_key=api_key).aio as client:
        yield client


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    if _gemini_api_key():
        log.info("Gemini NL agent configured with model %s", DEFAULT_GEMINI_MODEL)
    else:
        log.warning("GEMINI_API_KEY is not configured; chat completions will return 503.")
    yield


app = FastAPI(title="Gemini Natural Language Agent", version="3.0.0", lifespan=lifespan)


@app.middleware("http")
async def _require_api_key(request: Request, call_next):
    if request.url.path in {"/health", "/docs", "/openapi.json"} or request.url.path.startswith(
        "/docs"
    ):
        return await call_next(request)
    key = request.headers.get("X-API-Key") or request.headers.get("X-API-KEY")
    if not API_KEY or key != API_KEY:
        return JSONResponse(status_code=403, content={"detail": "Forbidden"})
    return await call_next(request)


def get_system_prompt() -> str:
    """Generate the base system prompt with the list of available tools."""
    tool_list = json.dumps(
        [
            {
                "name": name,
                "description": details["description"],
                "parameters": details["payload"],
            }
            for name, details in AVAILABLE_TOOLS.items()
        ],
        indent=2,
    )

    return f"""You are a helpful AI assistant that can use tools to answer questions.

You have access to the following tools:
{tool_list}

When you need a tool, choose exactly one tool and provide only the parameters required for that tool.
When you have enough information, provide a direct, concise answer for the user."""


def _format_messages(messages: List[Dict[str, str]]) -> str:
    return "\n\n".join(
        f"{message['role'].upper()}: {message['content']}" for message in messages
    )


def _sse_payload(
    completion_id: str,
    model: str,
    content: str = "",
    finish_reason: Optional[str] = None,
) -> str:
    payload = {
        "id": completion_id,
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": {"content": content} if content else {},
                "finish_reason": finish_reason,
            }
        ],
    }
    return f"data: {json.dumps(payload)}\n\n"


def _build_non_stream_response(content: str, model: str) -> Dict[str, Any]:
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
    }


async def call_tool(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Call a specified tool via the API gateway."""
    if tool_name not in AVAILABLE_TOOLS:
        log.warning("Attempted to call unknown tool: %s", tool_name)
        return {"error": f"Tool '{tool_name}' not found."}

    tool_info = AVAILABLE_TOOLS[tool_name]
    url = f"{GATEWAY_URL}{tool_info['endpoint']}"
    log.info("Calling tool %s at %s with params %s", tool_name, url, parameters)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url,
                json=parameters,
                timeout=60.0,
                headers={"X-API-KEY": API_KEY},
            )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as exc:
            log.error("Network error calling %s at %s: %s", tool_name, url, exc, exc_info=True)
            return {"error": f"Network error calling {tool_name}: {exc}"}
        except httpx.HTTPStatusError as exc:
            log.error(
                "HTTP error from %s at %s: %s - %s",
                tool_name,
                url,
                exc.response.status_code,
                exc.response.text,
                exc_info=True,
            )
            return {
                "error": (
                    f"Tool {tool_name} returned HTTP error "
                    f"{exc.response.status_code}: {exc.response.text}"
                )
            }
        except Exception as exc:
            log.error("Unexpected error calling %s at %s: %s", tool_name, url, exc, exc_info=True)
            return {"error": f"Unexpected error calling {tool_name}: {exc}"}


async def _plan_next_step(
    messages: List[Dict[str, str]],
    request: ChatCompletionRequest,
) -> ToolDecision:
    """Ask Gemini whether to use a tool or answer directly."""
    prompt = (
        "Conversation transcript:\n"
        f"{_format_messages(messages)}\n\n"
        "Decide the next action. "
        "If a tool is required, return action='tool' with one tool name and parameters. "
        "If you can answer now, return action='answer' with a direct final answer."
    )

    async with _get_async_client() as client:
        response = await client.models.generate_content(
            model=_selected_model(request.model),
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=get_system_prompt(),
                temperature=0,
                max_output_tokens=min(request.max_tokens or MAX_TOKENS, 512),
                response_mime_type="application/json",
                response_json_schema=TOOL_DECISION_SCHEMA,
            ),
        )

    raw_text = (response.text or "").strip()
    if not raw_text:
        raise RuntimeError("Gemini planner returned an empty response")
    return ToolDecision.model_validate(json.loads(raw_text))


async def _resolve_chat_completion(request: ChatCompletionRequest) -> str:
    """Resolve the chat request into a final assistant answer."""
    if not request.messages:
        raise HTTPException(status_code=400, detail="At least one message is required.")
    if not _gemini_api_key():
        raise HTTPException(status_code=503, detail="GEMINI_API_KEY is not configured.")

    messages = [message.model_dump() for message in request.messages]

    for iteration in range(5):
        log.debug("Tool loop iteration %s with messages %s", iteration + 1, messages)
        decision = await _plan_next_step(messages, request)

        if decision.action == "answer":
            answer = (decision.answer or "").strip()
            if answer:
                return answer
            raise RuntimeError("Gemini answer action did not include answer text")

        if not decision.tool:
            raise RuntimeError("Gemini tool action did not include a tool name")

        if decision.tool == "execute_shell" and SHELL_CONFIRMATION_REQUIRED:
            log.warning(
                "Shell command requested while confirmation is required; proceeding with current service semantics."
            )

        tool_result = await call_tool(decision.tool, decision.parameters)
        messages.append(
            {
                "role": "assistant",
                "content": json.dumps(
                    {
                        "action": decision.action,
                        "tool": decision.tool,
                        "parameters": decision.parameters,
                    }
                ),
            }
        )
        messages.append({"role": "tool", "content": json.dumps(tool_result)})

    log.warning("Max tool calls reached without a final answer.")
    return "Max tool calls reached. Please try again with a more specific query."


async def _stream_chat_completion(content: str, model: str) -> AsyncGenerator[str, None]:
    """Emit OpenAI-style SSE chunks for a completed response."""
    completion_id = f"chatcmpl-{uuid.uuid4().hex}"
    chunk_size = 80

    for index in range(0, len(content), chunk_size):
        yield _sse_payload(
            completion_id=completion_id,
            model=model,
            content=content[index : index + chunk_size],
        )
        await asyncio.sleep(0)

    yield _sse_payload(completion_id=completion_id, model=model, finish_reason="stop")
    yield "data: [DONE]\n\n"


@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "backend": "gemini",
        "model_status": "configured" if _gemini_api_key() else "missing_api_key",
        "model": DEFAULT_GEMINI_MODEL,
    }


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    answer = await _resolve_chat_completion(request)
    model = _selected_model(request.model)
    if request.stream:
        return StreamingResponse(
            _stream_chat_completion(answer, model),
            media_type="text/event-stream",
        )
    return _build_non_stream_response(answer, model)

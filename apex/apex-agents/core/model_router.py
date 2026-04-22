# apex-agents/core/model_router.py
from __future__ import annotations
import os
import json
from typing import Any, TypeVar, Type
from pydantic import BaseModel

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.runnables import RunnableSerializable


T = TypeVar("T", bound=BaseModel)


PROVIDER = os.getenv("LLM_PROVIDER", "openai").lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

AGENT_MODEL_MAP = {
    "research": os.getenv("MODEL_RESEARCH", "gpt-4o"),
    "creative": os.getenv("MODEL_CREATIVE", "gpt-4o"),
    "analytics": os.getenv("MODEL_ANALYTICS", "gpt-4o"),
    "sales": os.getenv("MODEL_SALES", "gpt-4o"),
    "hostile_auditor": os.getenv("MODEL_AUDIT", "gpt-4o"),
    "evolver": os.getenv("MODEL_EVOLVER", "gpt-4o"),
    "debate": os.getenv("MODEL_DEBATE", "gpt-4o"),
    "layer1": os.getenv("MODEL_LAYER1", "gpt-4o"),
    "layer2": os.getenv("MODEL_LAYER2", "gpt-4o"),
}


class _StructuredModel:
    def __init__(self, model: RunnableSerializable, schema: Type[BaseModel]):
        self._model = model
        self._schema = schema

    async def ainvoke(self, messages: list, config: dict | None = None) -> BaseModel:
        chain = self._model.with_structured_output(self._schema)
        result = await chain.ainvoke(messages, config=config)
        return result


class _LazyModel:
    def __init__(self, agent_name: str):
        self._agent_name = agent_name
        self._instance: RunnableSerializable | None = None

    def _get_model_class(self):
        if PROVIDER == "anthropic":
            return ChatAnthropic
        return ChatOpenAI

    def _get_model_kwargs(self):
        model_name = AGENT_MODEL_MAP.get(self._agent_name, "gpt-4o")
        if PROVIDER == "anthropic":
            api_key = ANTHROPIC_API_KEY
            return {"model": "claude-sonnet-4-20250514", "api_key": api_key}
        api_key = OPENAI_API_KEY
        return {"model": model_name, "api_key": api_key}

    def _ensure_instance(self):
        if self._instance is None:
            cls = self._get_model_class()
            kwargs = self._get_model_kwargs()
            self._instance = cls(**kwargs)
        return self._instance

    def with_structured_output(self, schema: Type[BaseModel]) -> _StructuredModel:
        return _StructuredModel(self._ensure_instance(), schema)

    async def ainvoke(self, messages: list, config: dict | None = None) -> Any:
        return await self._ensure_instance().ainvoke(messages, config=config or {})


class ModelRouter:
    @staticmethod
    def get_for_agent(agent_name: str) -> _LazyModel:
        return _LazyModel(agent_name)

"""Pydantic request/response models for all 7 ops domains."""

from typing import Any, Optional
from pydantic import BaseModel, Field


# ── Incidents ──────────────────────────────────────────────────────────────

class IncidentCreate(BaseModel):
    title: str = Field(..., max_length=200)
    severity: str = Field(default="SEV-2", pattern="^SEV-[1-4]$")
    blast_radius: str = Field(default="", max_length=500)


class IncidentPhaseAdvance(BaseModel):
    phase: str = Field(..., pattern="^(triage|evidence|containment|investigation|mitigation|stabilization|resolved)$")
    note: str = Field(default="", max_length=1000)


class IncidentResolve(BaseModel):
    root_cause: str = Field(..., max_length=1000)


# ── Debt ──────────────────────────────────────────────────────────────────

class DebtItemCreate(BaseModel):
    name: str = Field(..., max_length=200)
    description: str = Field(default="", max_length=1000)
    interest_per_year: float = Field(..., ge=0, description="Annual cost in dollars if NOT fixed")
    principal_cost: float = Field(..., ge=0, description="Cost in dollars to fix")


class DebtStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(open|in_progress|resolved)$")


# ── Costs ──────────────────────────────────────────────────────────────────

class CostSnapshotCreate(BaseModel):
    service_name: str = Field(..., max_length=100)
    monthly_cost: float = Field(..., ge=0)
    savings_opportunity: float = Field(default=0, ge=0)
    category: str = Field(default="compute", pattern="^(compute|storage|transfer|database|other)$")
    notes: str = Field(default="", max_length=500)


# ── Pipelines ──────────────────────────────────────────────────────────────

class PipelineUpsert(BaseModel):
    name: str = Field(..., max_length=200)
    status: str = Field(default="healthy", pattern="^(healthy|degraded|failed|unknown)$")
    quality_score: float = Field(default=100, ge=0, le=100)
    cost_per_record: float = Field(default=0, ge=0)
    records_per_day: int = Field(default=0, ge=0)
    sla_minutes: int = Field(default=60, ge=1)
    phase: str = Field(default="ingestion", pattern="^(ingestion|transformation|delivery|monitoring)$")


# ── Performance ────────────────────────────────────────────────────────────

class PerformanceItemCreate(BaseModel):
    service: str = Field(..., max_length=100)
    metric: str = Field(..., max_length=100, description="e.g. p99_latency, throughput, memory")
    current_value: float
    baseline_value: float
    unit: str = Field(default="ms", max_length=20)
    bottleneck: str = Field(default="", max_length=500)


class PerformanceResolve(BaseModel):
    root_cause: str = Field(..., max_length=1000)


# ── Migrations ─────────────────────────────────────────────────────────────

class MigrationCreate(BaseModel):
    name: str = Field(..., max_length=200)
    risk_level: str = Field(default="medium", pattern="^(low|medium|high|critical)$")


class MigrationPhaseAdvance(BaseModel):
    phase: str = Field(..., pattern="^(scope|risk|architecture|rollback|validation|execution|completed)$")
    rollback_ready: bool = Field(default=False)
    kill_switch: bool = Field(default=False)
    validation_pct: float = Field(default=0, ge=0, le=100)


# ── API Contracts ──────────────────────────────────────────────────────────

class APIContractCreate(BaseModel):
    endpoint: str = Field(..., max_length=300)
    version: str = Field(default="v1", max_length=20)
    method: str = Field(default="GET", pattern="^(GET|POST|PUT|PATCH|DELETE)$")
    service: str = Field(..., max_length=100)
    notes: str = Field(default="", max_length=500)


class APIContractCheck(BaseModel):
    breaking_changes: int = Field(default=0, ge=0)
    doc_complete: bool = Field(default=False)
    consistency_score: float = Field(default=100, ge=0, le=100)

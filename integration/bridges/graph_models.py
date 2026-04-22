"""
Pydantic models for graph operations.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime


class NodeCreateRequest(BaseModel):
    """Request to create a graph node."""
    id: str = Field(..., description="Unique node identifier")
    labels: List[str] = Field(default=["Entity"], description="Node labels")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Node properties")


class NodeResponse(BaseModel):
    """Response containing node data."""
    id: str
    labels: List[str]
    properties: Dict[str, Any]
    created_at: Optional[str] = None


class RelationshipCreateRequest(BaseModel):
    """Request to create a relationship."""
    id: str = Field(..., description="Unique relationship identifier")
    type: str = Field(..., description="Relationship type")
    start_node_id: str = Field(..., description="Start node ID")
    end_node_id: str = Field(..., description="End node ID")
    properties: Dict[str, Any] = Field(default_factory=dict)


class RelationshipResponse(BaseModel):
    """Response containing relationship data."""
    id: str
    type: str
    start_node_id: str
    end_node_id: str
    properties: Dict[str, Any]


class GraphQueryRequest(BaseModel):
    """Request to execute a Cypher query."""
    cypher: str = Field(..., description="Cypher query string")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    read_only: bool = Field(default=True, description="Whether query modifies data")


class GraphQueryResponse(BaseModel):
    """Response from graph query."""
    results: List[Dict[str, Any]]
    record_count: int
    execution_time_ms: Optional[float] = None


class GraphHealthResponse(BaseModel):
    """Health check response for graph service."""
    connected: bool
    neo4j_available: bool
    uri: str
    query_test: Optional[str] = None
    timestamp: str

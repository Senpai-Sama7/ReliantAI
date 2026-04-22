"""
Pydantic models for RAG (Retrieval Augmented Generation) operations.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class DocumentType(str, Enum):
    """Document types supported for ingestion."""
    PDF = "pdf"
    TXT = "txt"
    MD = "md"
    HTML = "html"
    JSON = "json"


class DocumentIngestRequest(BaseModel):
    """Request to ingest a document."""
    document_id: str = Field(..., description="Unique document identifier")
    content: str = Field(..., description="Document content")
    doc_type: DocumentType = Field(default=DocumentType.TXT)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    source: Optional[str] = Field(default=None, description="Document source URL/path")


class DocumentIngestResponse(BaseModel):
    """Response from document ingestion."""
    document_id: str
    status: str
    chunks_created: int
    embedding_dim: int
    timestamp: str


class SearchRequest(BaseModel):
    """Request for semantic search."""
    query: str = Field(..., description="Search query text", min_length=1)
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results")
    filter_metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata filters")
    min_similarity: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")


class SearchResult(BaseModel):
    """Single search result."""
    document_id: str
    chunk_id: str
    content: str
    similarity: float
    metadata: Dict[str, Any]


class SearchResponse(BaseModel):
    """Response from semantic search."""
    query: str
    results: List[SearchResult]
    total_results: int
    search_time_ms: float
    timestamp: str


class RAGQueryRequest(BaseModel):
    """Request for RAG-enhanced query."""
    question: str = Field(..., description="User question", min_length=1)
    context_chunks: int = Field(default=3, ge=1, le=10, description="Number of context chunks")
    include_sources: bool = Field(default=True, description="Include source references")


class RAGQueryResponse(BaseModel):
    """Response from RAG query."""
    question: str
    answer: str
    sources: List[Dict[str, Any]]
    context_used: List[str]
    confidence: float
    query_time_ms: float
    timestamp: str


class DocumentStats(BaseModel):
    """Document statistics."""
    total_documents: int
    total_chunks: int
    document_types: Dict[str, int]
    avg_chunk_size: float
    last_updated: Optional[str]


class RAGHealthResponse(BaseModel):
    """Health check response for RAG service."""
    status: str
    database_connected: bool
    pgvector_available: bool
    documents_indexed: int
    embedding_model: str
    timestamp: str

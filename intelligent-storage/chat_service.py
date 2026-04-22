"""
Chat Service for Intelligent Storage Nexus
Implements Retrieval-Augmented Generation (RAG) using the existing search & index infrastructure.
"""

import logging
from typing import List, Dict, AsyncGenerator, Optional

from config import EMBED_MODEL, EMBED_DIM
from db import get_conn
import gemini_client

logger = logging.getLogger(__name__)


def normalize_query_text(query: str) -> str:
    """Normalize user query text for deterministic embedding calls."""
    return " ".join((query or "").strip().split())


async def get_embedding(text: str) -> Optional[List[float]]:
    """
    Retrieve an embedding from Gemini.

    This lives in chat_service to avoid importing api_server and causing
    circular imports in /api/chat.
    """
    normalized = normalize_query_text(text)
    if not normalized:
        return None

    return await gemini_client.get_single_embedding(normalized)

async def chat_with_data(mapped_query: str, history: List[Dict[str, str]], context_window: int = 5) -> AsyncGenerator[str, None]:
    """
    Stream chat responses using RAG.
    
    Args:
        mapped_query: The user's latest question
        history: Chat history (list of {"role": "user"|"assistant", "content": "..."})
        context_window: Number of previous messages to include
        
    Yields:
        Chunks of the response text
    """
    
    # 1. Retrieve relevant context (using granular chunks)
    context_docs = await retrieve_context(mapped_query)
    
    # 2. Construct Prompt
    system_prompt = construct_system_prompt(context_docs)
    
    # 3. Format messages for Gemini
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Add recent history for continuity
    for msg in history[-context_window:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    messages.append({"role": "user", "content": mapped_query})
    
    # 4. Stream response from Gemini
    async for chunk in gemini_client.stream_chat(messages):
        yield chunk

async def retrieve_context(query: str, limit: int = 7) -> List[Dict]:
    """
    Retrieve relevant file chunks or file previews for the query using semantic search.
    """
    normalized_query = normalize_query_text(query)
    query_vec = await get_embedding(normalized_query)
    
    if query_vec is None:
        logger.warning(f"Could not generate embedding for query: {query}")
        return []

    async with get_conn() as conn:
        # Check if chunk table exists and has data (Phase 3D).
        chunk_table_exists = await conn.fetchval(
            "SELECT to_regclass('public.file_chunks') IS NOT NULL"
        )
        chunk_exists = False
        if chunk_table_exists:
            chunk_exists = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM file_chunks LIMIT 1)"
            )
        
        if chunk_exists:
            # Search file_chunks for better granularity
            rows = await conn.fetch(
                """
                SELECT 
                    f.name, 
                    f.path, 
                    fc.content as context,
                    1 - (fc.embedding <=> $1::vector(768)) as score
                FROM file_chunks fc
                JOIN files f ON fc.file_id = f.id
                WHERE fc.embedding IS NOT NULL
                ORDER BY fc.embedding <=> $1
                LIMIT $2
                """,
                str(list(query_vec)), 
                limit
            )
        else:
            # Fallback to file-level embeddings and content previews
            rows = await conn.fetch(
                """
                SELECT 
                    f.name, 
                    f.path, 
                    f.content_preview as context,
                    1 - (fe.embedding <=> $1::vector(768)) as score
                FROM file_embeddings fe
                JOIN files f ON fe.file_id = f.id
                WHERE fe.embedding IS NOT NULL
                  AND COALESCE(fe.model, $3) = $3
                ORDER BY fe.embedding <=> $1
                LIMIT $2
                """,
                str(list(query_vec)), 
                limit,
                EMBED_MODEL,
            )
        
        results = []
        for row in rows:
            results.append({
                "source": row["name"],
                "path": row["path"],
                "content": (row["context"] or "").strip(),
                "score": float(row["score"])
            })
            
        return results

    return results

# Phase 6G: Agentic Action Registry
AVAILABLE_ACTIONS = {
    "REINDEX": "/api/control/index",
    "FORCE_REINDEX": "/api/control/index?force=true",
    "CLEAR_DATABASE": "/api/control/clear-db",
    "SYSTEM_STATS": "/api/control/stats"
}

def construct_system_prompt(context_docs: List[Dict]) -> str:
    """Build the system prompt with retrieved context and agentic capabilities."""
    
    if not context_docs:
        context_str = "No specific file context found for this query."
    else:
        context_str = "\n\n".join([
            f"--- Source: {doc['source']} ({doc['path']}) ---\n{doc['content']}"
            for doc in context_docs
        ])
    
    return f"""You are the Intelligent Storage Nexus AI Assistant, a sophisticated agentic RAG system.
Your mission is to help the user manage and understand their files.

AVAILABLE FILE CONTEXT:
{context_str}

AGENTIC CAPABILITIES:
You have direct control over the system. If the user asks for a system action, you must include the corresponding action tag at the end of your response.
- To re-index files: `[ACTION: REINDEX]`
- To re-index EVERYTHING from scratch (force): `[ACTION: FORCE_REINDEX]`
- To wipe the database: `[ACTION: CLEAR_DATABASE]`
- To show detailed system stats: `[ACTION: SYSTEM_STATS]`

OPERATIONAL GUIDELINES:
1.  **Strict Context Adherence**: Base your answers ONLY on the provided context information.
2.  **Explicit Citations**: Mention file names using "[Source: filename]".
3.  **Action Triggering**: If a user asks "Re-scan my files" or "What's the status?", acknowledge the request and use the appropriate `[ACTION: ...]` tag.
4.  **Handling Uncertainty**: If context is missing, say: "I couldn't find details about that in your indexed files."
5.  **Tone**: Professional, technical, and proactive.
"""

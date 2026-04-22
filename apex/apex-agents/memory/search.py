# apex-agents/memory/search.py
from __future__ import annotations
import os
import asyncpg
from memory.embeddings import get_embedding, embedding_to_pg

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://apex:changeme@postgres:5432/apex_db"
)


async def search_memory(
    query:       str,
    memory_type: str = "all",
    limit:       int = 5,
) -> list[dict]:
    """
    Semantic similarity search against episodic_memory using pgvector.

    Uses cosine similarity: 1 - (embedding <=> query_embedding)
    The <=> operator returns cosine distance (0=identical, 2=opposite).
    We subtract from 1 to return similarity (1=identical, -1=opposite).

    The HNSW index on episodic_memory.embedding makes this ~5-10ms at scale.
    Rows without embeddings (legacy data before migration) are excluded via
    WHERE embedding IS NOT NULL.
    """
    embedding   = await get_embedding(query)
    pg_vec      = embedding_to_pg(embedding)
    type_clause = "" if memory_type == "all" else "AND memory_type = $3"

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        sql = f"""
            SELECT
                id::text,
                agent_name,
                task_summary,
                content,
                correction,
                outcome,
                memory_type,
                confidence,
                created_at,
                1 - (embedding <=> $1::vector) AS similarity
            FROM episodic_memory
            WHERE embedding IS NOT NULL
            {type_clause}
            ORDER BY embedding <=> $1::vector
            LIMIT $2
        """
        params = [pg_vec, limit] if memory_type == "all" else [pg_vec, limit, memory_type]
        rows   = await conn.fetch(sql, *params)
        return [
            {
                "id":           r["id"],
                "agent_name":   r["agent_name"],
                "task_summary": r["task_summary"],
                "content":      r["content"],
                "correction":   r["correction"],
                "outcome":      r["outcome"],
                "memory_type":  r["memory_type"],
                "confidence":   float(r["confidence"] or 0),
                "similarity":   round(float(r["similarity"]), 4),
                "created_at":   r["created_at"].isoformat(),
            }
            for r in rows
        ]
    finally:
        await conn.close()


async def save_memory(
    agent_name:   str,
    task_summary: str,
    content:      str,
    memory_type:  str,
    confidence:   float       = 0.8,
    correction:   str | None = None,
    outcome:      str | None = None,
) -> str:
    """
    Embeds and saves a memory row. Returns the new row's UUID as a string.

    Embedding is computed on f"{task_summary}: {content}" so that similarity
    search on task descriptions will surface this record. The colon-space
    separator is a simple concatenation signal that preserves both dimensions.
    """
    embedding = await get_embedding(f"{task_summary}: {content}")
    pg_vec    = embedding_to_pg(embedding)

    conn = await asyncpg.connect(DATABASE_URL)
    try:
        row = await conn.fetchrow(
            """
            INSERT INTO episodic_memory
                (agent_name, task_summary, content, memory_type,
                 confidence, correction, outcome, embedding)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8::vector)
            RETURNING id
            """,
            agent_name, task_summary, content, memory_type,
            confidence, correction, outcome, pg_vec,
        )
        return str(row["id"])
    finally:
        await conn.close()

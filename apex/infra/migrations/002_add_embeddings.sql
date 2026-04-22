-- infra/migrations/002_add_embeddings.sql
-- Run after 001_initial_schema.sql
-- Adds pgvector support and embedding column to episodic_memory.

CREATE EXTENSION IF NOT EXISTS vector;

ALTER TABLE episodic_memory
  ADD COLUMN IF NOT EXISTS embedding    vector(1536),
  ADD COLUMN IF NOT EXISTS memory_type  TEXT NOT NULL DEFAULT 'episodic',
  ADD COLUMN IF NOT EXISTS content      TEXT,
  ADD COLUMN IF NOT EXISTS correction   TEXT,
  ADD COLUMN IF NOT EXISTS outcome      TEXT;

-- HNSW chosen over IVFFlat:
-- IVFFlat requires VACUUM + training SELECT before index is effective.
-- HNSW builds incrementally with no training step and outperforms
-- IVFFlat at recall on datasets under ~10M rows.
-- m=16: graph connectivity (higher = better recall, more memory)
-- ef_construction=200: build-time search width (higher = better quality index)
CREATE INDEX IF NOT EXISTS episodic_memory_embedding_hnsw
  ON episodic_memory
  USING hnsw (embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 200);

COMMENT ON COLUMN episodic_memory.embedding IS
  'gemini-embedding-001 (1536-dim output) of "task_summary: content". Used for cosine similarity search via <=> operator.';

COMMENT ON COLUMN episodic_memory.memory_type IS
  'episodic | semantic | procedural. episodic = past decisions, semantic = domain knowledge, procedural = how-to.';

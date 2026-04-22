-- HNSW Index Tuning Migration
-- For 768-dim vectors with ~350K rows
-- REQUIRES: Run as postgres superuser or table owner
--
-- Usage:
--   psql -h localhost -p 5433 -U postgres -d intelligent_storage -f migrations/001_hnsw_tuning.sql

BEGIN;

-- Grant ownership so storage_admin can manage indexes going forward
ALTER TABLE file_embeddings OWNER TO storage_admin;
ALTER TABLE agent_memories OWNER TO storage_admin;

-- Drop the default-param index
DROP INDEX IF EXISTS idx_embed_vec;

-- Recreate with tuned parameters
-- m=24: more connections per layer (default 16) → better recall
-- ef_construction=200: more candidates during build (default 64) → better quality
CREATE INDEX idx_embed_vec ON file_embeddings
  USING hnsw(embedding vector_cosine_ops)
  WITH (m = 24, ef_construction = 200);

-- Set search-time ef (higher = better recall, slower search)
ALTER SYSTEM SET hnsw.ef_search = 100;
SELECT pg_reload_conf();

-- Also tune the agent_memories HNSW index
DROP INDEX IF EXISTS idx_mem_vec;
CREATE INDEX idx_mem_vec ON agent_memories
  USING hnsw(embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 128);

COMMIT;

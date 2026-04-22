-- Intelligent Storage System - Database Schema
-- PostgreSQL 17 + pgvector + Apache AGE

-- Need pg_trgm for fuzzy matching
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS vector;

SET search_path = public;

-- ============================================================
-- CORE FILE METADATA
-- ============================================================

CREATE TABLE IF NOT EXISTS directories (
    id BIGSERIAL PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    parent_id BIGINT REFERENCES directories(id),
    partition TEXT NOT NULL DEFAULT 'DATA_HUB',
    depth INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_dir_parent ON directories(parent_id);
CREATE INDEX idx_dir_path ON directories USING gin(path gin_trgm_ops);

CREATE TABLE IF NOT EXISTS files (
    id BIGSERIAL PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    extension TEXT,
    directory_id BIGINT REFERENCES directories(id),
    size_bytes BIGINT,
    mime_type TEXT,
    sha256 TEXT,
    partition TEXT NOT NULL DEFAULT 'DATA_HUB',
    file_modified_at TIMESTAMPTZ,
    indexed_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    metadata JSONB DEFAULT '{}',
    content_preview TEXT,
    chunk_count INT DEFAULT 0,
    fts_vector TSVECTOR
);
CREATE INDEX idx_files_dir ON files(directory_id);
CREATE INDEX idx_files_ext ON files(extension);
CREATE INDEX idx_files_mime ON files(mime_type);
CREATE INDEX idx_files_name ON files USING gin(name gin_trgm_ops);
CREATE INDEX idx_files_path ON files USING gin(path gin_trgm_ops);
CREATE INDEX idx_files_fts ON files USING gin(fts_vector);
CREATE INDEX idx_files_meta ON files USING gin(metadata jsonb_path_ops);
CREATE INDEX idx_files_sha ON files(sha256);

-- Auto-update fts_vector
CREATE OR REPLACE FUNCTION update_fts_vector() RETURNS TRIGGER AS $$
BEGIN
    NEW.fts_vector := to_tsvector('english',
        coalesce(NEW.name, '') || ' ' ||
        coalesce(NEW.path, '') || ' ' ||
        coalesce(NEW.content_preview, '') || ' ' ||
        coalesce(NEW.metadata->>'tags', '') || ' ' ||
        coalesce(NEW.metadata->>'category', '')
    );
    NEW.updated_at := now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_files_fts
    BEFORE INSERT OR UPDATE ON files
    FOR EACH ROW EXECUTE FUNCTION update_fts_vector();

-- ============================================================
-- VECTOR EMBEDDINGS (768d nomic-embed-text)
-- ============================================================

CREATE TABLE IF NOT EXISTS file_embeddings (
    id BIGSERIAL PRIMARY KEY,
    file_id BIGINT REFERENCES files(id) ON DELETE CASCADE UNIQUE,
    embedding vector(768) NOT NULL,
    model TEXT NOT NULL DEFAULT 'nomic-embed-text',
    created_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_embed_file ON file_embeddings(file_id);
CREATE INDEX idx_embeddings_model ON file_embeddings(model);
CREATE INDEX IF NOT EXISTS idx_embed_vec ON file_embeddings USING hnsw(embedding vector_cosine_ops) WITH (m = 16, ef_construction = 128);

-- ============================================================
-- CONTENT CHUNKS (For granular semantic search)
-- ============================================================

CREATE TABLE IF NOT EXISTS file_chunks (
    id BIGSERIAL PRIMARY KEY,
    file_id BIGINT REFERENCES files(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    content TEXT,
    embedding vector(768),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(file_id, chunk_index)
);
CREATE INDEX IF NOT EXISTS idx_file_chunks_file_id ON file_chunks(file_id);
CREATE INDEX IF NOT EXISTS idx_file_chunks_embedding ON file_chunks USING hnsw(embedding vector_cosine_ops) WITH (m = 16, ef_construction = 128);

COMMENT ON TABLE file_chunks IS 'Stores content chunks of files with individual embeddings for granular search';

-- ============================================================
-- TAGGING & CATEGORIZATION
-- ============================================================

CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    category TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS file_tags (
    file_id BIGINT REFERENCES files(id) ON DELETE CASCADE,
    tag_id INT REFERENCES tags(id) ON DELETE CASCADE,
    confidence REAL DEFAULT 1.0,
    source TEXT DEFAULT 'auto',
    PRIMARY KEY (file_id, tag_id)
);

-- ============================================================
-- AI AGENT MEMORY LAYER
-- ============================================================

CREATE TABLE IF NOT EXISTS agent_memories (
    id BIGSERIAL PRIMARY KEY,
    agent_id TEXT NOT NULL DEFAULT 'default',
    memory_type TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(768),
    metadata JSONB DEFAULT '{}',
    importance REAL DEFAULT 0.5,
    access_count INT DEFAULT 0,
    last_accessed TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT now(),
    expires_at TIMESTAMPTZ
);
CREATE INDEX idx_mem_agent ON agent_memories(agent_id);
CREATE INDEX idx_mem_type ON agent_memories(memory_type);
CREATE INDEX idx_mem_vec ON agent_memories USING hnsw(embedding vector_cosine_ops);
CREATE INDEX idx_mem_importance ON agent_memories(importance DESC);

-- ============================================================
-- HYBRID SEARCH FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION hybrid_search(
    query_text TEXT,
    query_embedding vector(768),
    result_limit INT DEFAULT 20,
    semantic_weight REAL DEFAULT 0.5,
    keyword_weight REAL DEFAULT 0.3,
    meta_weight REAL DEFAULT 0.2,
    p_model TEXT DEFAULT 'nomic-embed-text'
) RETURNS TABLE(
    file_id BIGINT,
    file_path TEXT,
    file_name TEXT,
    score REAL,
    semantic_score REAL,
    keyword_score REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        f.id,
        f.path,
        f.name,
        (
            coalesce(semantic_weight * (1 - (fe.embedding <=> query_embedding)), 0) +
            coalesce(keyword_weight * ts_rank(f.fts_vector, plainto_tsquery('english', query_text)), 0) +
            coalesce(meta_weight * similarity(f.name, query_text), 0)
        )::REAL AS score,
        coalesce((1 - (fe.embedding <=> query_embedding))::REAL, 0),
        coalesce(ts_rank(f.fts_vector, plainto_tsquery('english', query_text))::REAL, 0)
    FROM files f
    LEFT JOIN file_embeddings fe 
      ON fe.file_id = f.id 
     AND COALESCE(fe.model, p_model) = p_model
    WHERE f.fts_vector @@ plainto_tsquery('english', query_text)
       OR (fe.embedding IS NOT NULL AND fe.embedding <=> query_embedding < 0.7)
       OR similarity(f.name, query_text) > 0.1
    ORDER BY score DESC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- MEMORY RECALL FUNCTION
-- ============================================================

CREATE OR REPLACE FUNCTION recall_memories(
    p_agent_id TEXT,
    p_query_embedding vector(768),
    p_limit INT DEFAULT 10
) RETURNS TABLE(
    memory_id BIGINT,
    content TEXT,
    memory_type TEXT,
    relevance REAL,
    importance REAL
) AS $$
BEGIN
    UPDATE agent_memories SET access_count = access_count + 1, last_accessed = now()
    WHERE agent_id = p_agent_id
      AND (expires_at IS NULL OR expires_at > now());

    RETURN QUERY
    SELECT m.id, m.content, m.memory_type,
        (1 - (m.embedding <=> p_query_embedding))::REAL,
        m.importance
    FROM agent_memories m
    WHERE m.agent_id = p_agent_id
      AND (m.expires_at IS NULL OR m.expires_at > now())
    ORDER BY (0.7 * (1 - (m.embedding <=> p_query_embedding)) + 0.3 * m.importance) DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- KNOWLEDGE GRAPH (Apache AGE)
-- ============================================================

DO $$
BEGIN
    BEGIN
        CREATE EXTENSION IF NOT EXISTS age;
        EXECUTE 'SET search_path = ag_catalog, public';

        IF NOT EXISTS (
            SELECT 1 FROM ag_catalog.ag_graph WHERE name = 'storage_graph'
        ) THEN
            PERFORM ag_catalog.create_graph('storage_graph');
        END IF;
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'Apache AGE not configured; continuing without AGE graph: %', SQLERRM;
    END;
END
$$;

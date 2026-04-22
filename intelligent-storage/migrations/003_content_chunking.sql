-- Phase 3D: Content-aware chunking
-- Creates table for file chunks with individual embeddings

-- Create file_chunks table
CREATE TABLE IF NOT EXISTS file_chunks (
    id BIGSERIAL PRIMARY KEY,
    file_id BIGINT REFERENCES files(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    content TEXT,
    embedding vector(768),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(file_id, chunk_index)
);

-- Index for fast lookup by file_id
CREATE INDEX IF NOT EXISTS idx_file_chunks_file_id ON file_chunks(file_id);

-- Index for vector similarity search on chunks
CREATE INDEX IF NOT EXISTS idx_file_chunks_embedding ON file_chunks USING hnsw(embedding vector_cosine_ops);

-- Add chunk_count column to files table to track number of chunks
ALTER TABLE files ADD COLUMN IF NOT EXISTS chunk_count INT DEFAULT 0;

COMMENT ON TABLE file_chunks IS 'Stores content chunks of files with individual embeddings for granular search';

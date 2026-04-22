-- Migration: Ensure embedding model tracking uses file_embeddings.model
-- Created: 2026-02-11
-- Phase: 5B - schema alignment for model-aware retrieval

-- Ensure model column exists and is populated.
ALTER TABLE file_embeddings
ADD COLUMN IF NOT EXISTS model TEXT;

UPDATE file_embeddings
SET model = 'nomic-embed-text'
WHERE model IS NULL OR model = '';

ALTER TABLE file_embeddings
ALTER COLUMN model SET DEFAULT 'nomic-embed-text';

-- Add index for efficient model-based queries.
CREATE INDEX IF NOT EXISTS idx_embeddings_model
ON file_embeddings(model);

-- Create view for files missing embeddings for the active/default model.
CREATE OR REPLACE VIEW files_missing_new_embeddings AS
SELECT f.id, f.name, f.path, f.extension, f.content_preview, f.updated_at
FROM files f
LEFT JOIN file_embeddings fe ON f.id = fe.file_id
    AND fe.model = 'nomic-embed-text'
WHERE fe.file_id IS NULL;

COMMENT ON COLUMN file_embeddings.model IS
    'Tracks which embedding model generated this vector (e.g., nomic-embed-text, mxbai-embed-large)';

-- Verify migration.
SELECT
    'Migration complete' as status,
    COUNT(*) as total_embeddings,
    COUNT(DISTINCT model) as model_count,
    model as primary_model
FROM file_embeddings
GROUP BY model
ORDER BY COUNT(*) DESC
LIMIT 1;

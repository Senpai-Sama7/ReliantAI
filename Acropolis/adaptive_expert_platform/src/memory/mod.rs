//! Enhanced memory system with real embeddings and improved performance.

use anyhow::{anyhow, Result};
use blake3::Hasher;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use tracing::{debug, warn, instrument};

// Re-export the redis store module and core traits
pub mod redis_store;
pub use redis_store::{EmbeddingCache, CacheStats};

use crate::agent::Agent;

/// Memory fragment with enhanced metadata
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryFragment {
    pub content: String,
    pub embedding: Vec<f32>,
    pub metadata: HashMap<String, serde_json::Value>,
    pub timestamp: u64,
    pub source: String,
    pub tags: Vec<String>,
}

impl MemoryFragment {
    pub fn new(content: String, embedding: Vec<f32>) -> Self {
        Self {
            content,
            embedding,
            metadata: HashMap::new(),
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap_or_default()
                .as_secs(),
            source: "manual".to_string(),
            tags: Vec::new(),
        }
    }

    pub fn with_metadata(mut self, metadata: HashMap<String, serde_json::Value>) -> Self {
        self.metadata = metadata;
        self
    }

    pub fn with_source(mut self, source: String) -> Self {
        self.source = source;
        self
    }

    pub fn with_tags(mut self, tags: Vec<String>) -> Self {
        self.tags = tags;
        self
    }
}

/// Enhanced memory system with real embeddings and improved performance
pub struct Memory {
    embedding_agent: Arc<dyn Agent>,
    reranker_agent: Arc<dyn Agent>,
    cache: Arc<dyn EmbeddingCache + Send + Sync>,
    fragments: RwLock<Vec<MemoryFragment>>,
    kv_store: RwLock<HashMap<String, serde_json::Value>>,
    max_fragments: usize,
    embedding_dim: usize,
    similarity_threshold: f32,
}

impl std::fmt::Debug for Memory {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("Memory")
            .field("max_fragments", &self.max_fragments)
            .field("embedding_dim", &self.embedding_dim)
            .field("similarity_threshold", &self.similarity_threshold)
            .finish_non_exhaustive()
    }
}

impl Memory {
    pub fn new(
        embedding_agent: Arc<dyn Agent>,
        reranker_agent: Arc<dyn Agent>,
        cache: Arc<dyn EmbeddingCache>,
    ) -> Self {
        Self {
            embedding_agent,
            reranker_agent,
            cache,
            fragments: RwLock::new(Vec::new()),
            kv_store: RwLock::new(HashMap::new()),
            max_fragments: 10_000,
            embedding_dim: 384, // Default embedding dimension
            similarity_threshold: 0.1,
        }
    }

    pub fn with_max_fragments(mut self, max_fragments: usize) -> Self {
        self.max_fragments = max_fragments;
        self
    }

    pub fn with_embedding_dim(mut self, embedding_dim: usize) -> Self {
        self.embedding_dim = embedding_dim;
        self
    }

    pub fn with_similarity_threshold(mut self, threshold: f32) -> Self {
        self.similarity_threshold = threshold;
        self
    }

    /// Adds a fragment with real embedding generation
    #[instrument(skip(self))]
    pub async fn add_memory(&self, content: &str) -> Result<()> {
        if content.trim().is_empty() {
            return Err(anyhow!("Cannot add empty content to memory"));
        }

        let key = cache_key(content);
        let embedding = if let Some(vec) = self.cache.get(&key).await? {
            debug!("Using cached embedding for content");
            vec
        } else {
            debug!("Computing new embedding for content");

            // Generate real embedding using the embedding agent
            let embedding_input = serde_json::json!({
                "text": content,
                "task": "embedding"
            });

            let embedding_result = self.embedding_agent
                .handle(embedding_input, Arc::new(self.clone_dummy_memory()))
                .await?;

            let vec: Vec<f32> = serde_json::from_str(&embedding_result)
                .map_err(|e| anyhow!("Failed to parse embedding JSON: {}", e))?;

            if vec.is_empty() {
                return Err(anyhow!("Embedding agent returned empty vector"));
            }

            if vec.len() != self.embedding_dim {
                warn!("Embedding dimension mismatch: expected {}, got {}", self.embedding_dim, vec.len());
            }

            self.cache.set(&key, &vec).await?;
            vec
        };

        let mut fragments = self.fragments.write().await;

        // Enforce max fragments limit with LRU eviction
        if fragments.len() >= self.max_fragments {
            debug!("Memory at capacity, removing oldest fragment");
            fragments.remove(0); // Remove oldest
        }

        fragments.push(MemoryFragment::new(content.to_owned(), embedding));
        debug!("Added memory fragment, total fragments: {}", fragments.len());
        Ok(())
    }

    /// Enhanced memory search with reranking
    #[instrument(skip(self))]
    pub async fn search_memory(&self, query: &str, top_k: usize) -> Result<Vec<String>> {
        if query.trim().is_empty() {
            return Ok(vec![]);
        }

        let key = cache_key(query);
        let q_emb = if let Some(v) = self.cache.get(&key).await? {
            v
        } else {
            // Generate embedding for query
            let query_input = serde_json::json!({
                "text": query,
                "task": "embedding"
            });

            let embedding_result = self.embedding_agent
                .handle(query_input, Arc::new(self.clone_dummy_memory()))
                .await?;

            let vec: Vec<f32> = serde_json::from_str(&embedding_result)
                .map_err(|e| anyhow!("Failed to parse query embedding JSON: {}", e))?;

            self.cache.set(&key, &vec).await?;
            vec
        };

        let frags = self.fragments.read().await;
        if frags.is_empty() {
            debug!("No fragments in memory for search");
            return Ok(vec![]);
        }

        // First pass: vector similarity search
        let mut scored: Vec<(f32, &MemoryFragment)> = frags
            .iter()
            .map(|f| (cosine(&q_emb, &f.embedding), f))
            .filter(|(score, _)| *score > self.similarity_threshold)
            .collect();

        scored.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap_or(std::cmp::Ordering::Equal));

        // Take top candidates for reranking
        let candidates: Vec<String> = scored
            .into_iter()
            .take(top_k * 2) // Get more candidates for reranking
            .map(|(_, fragment)| fragment.content.clone())
            .collect();

        if candidates.is_empty() {
            return Ok(vec![]);
        }

        // Second pass: rerank using reranker agent
        let rerank_input = serde_json::json!({
            "query": query,
            "candidates": candidates,
            "task": "rerank"
        });

        let rerank_result = self.reranker_agent
            .handle(rerank_input, Arc::new(self.clone_dummy_memory()))
            .await?;

        // Parse reranked results
        let reranked: Vec<String> = serde_json::from_str(&rerank_result)
            .map_err(|e| anyhow!("Failed to parse rerank result: {}", e))?;

        let final_results: Vec<_> = reranked.into_iter().take(top_k).collect();
        debug!("Memory search returned {} results", final_results.len());
        Ok(final_results)
    }

    /// Get memory statistics
    pub async fn stats(&self) -> MemoryStats {
        let fragments = self.fragments.read().await;
        let (cache_hits, cache_misses) = match self.cache.stats().await {
            Ok(stats) => (stats.hits, stats.misses),
            Err(_) => (0, 0),
        };

        let total_cache_accesses = cache_hits + cache_misses;
        MemoryStats {
            total_fragments: fragments.len(),
            cache_hits,
            cache_misses,
            cache_hit_rate: if total_cache_accesses > 0 {
                cache_hits as f64 / total_cache_accesses as f64
            } else {
                0.0
            },
            memory_usage_mb: (fragments.len() * self.embedding_dim * 4) as f64 / (1024.0 * 1024.0),
            embedding_dim: self.embedding_dim,
            similarity_threshold: self.similarity_threshold,
        }
    }

    /// Clear all memory
    pub async fn clear(&self) -> Result<()> {
        let mut fragments = self.fragments.write().await;
        fragments.clear();

        let mut kv_store = self.kv_store.write().await;
        kv_store.clear();

        self.cache.clear().await?;
        debug!("Memory cleared");
        Ok(())
    }

    /// Set key-value pair
    pub async fn set_kv(&self, key: &str, value: serde_json::Value) -> Result<()> {
        let mut kv_store = self.kv_store.write().await;
        kv_store.insert(key.to_string(), value);
        Ok(())
    }

    /// Get key-value pair
    pub async fn get_kv(&self, key: &str) -> Result<Option<serde_json::Value>> {
        let kv_store = self.kv_store.read().await;
        Ok(kv_store.get(key).cloned())
    }

    /// Create a dummy memory for embedding calls to avoid circular dependency
    fn clone_dummy_memory(&self) -> Self {
        Self {
            embedding_agent: self.embedding_agent.clone(),
            reranker_agent: self.reranker_agent.clone(),
            cache: self.cache.clone(),
            fragments: RwLock::new(Vec::new()),
            kv_store: RwLock::new(HashMap::new()),
            max_fragments: 0, // Empty for dummy
            embedding_dim: self.embedding_dim,
            similarity_threshold: self.similarity_threshold,
        }
    }

    /// Get the number of memory fragments
    pub async fn get_fragment_count(&self) -> usize {
        self.fragments.read().await.len()
    }
}

/// Memory statistics
#[derive(Debug, Clone, Serialize)]
pub struct MemoryStats {
    pub total_fragments: usize,
    pub cache_hits: u64,
    pub cache_misses: u64,
    pub cache_hit_rate: f64,
    pub memory_usage_mb: f64,
    pub embedding_dim: usize,
    pub similarity_threshold: f32,
}

/// Create a Blake3 hash key for content.
fn cache_key(content: &str) -> String {
    let mut hasher = Hasher::new();
    hasher.update(content.as_bytes());
    format!("embedding:{}", hasher.finalize().to_hex())
}

/// Compute cosine similarity between two vectors.
fn cosine(a: &[f32], b: &[f32]) -> f32 {
    if a.len() != b.len() || a.is_empty() {
        return 0.0;
    }

    let dot_product: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let norm_a: f32 = a.iter().map(|x| x * x).sum::<f32>().sqrt();
    let norm_b: f32 = b.iter().map(|x| x * x).sum::<f32>().sqrt();

    if norm_a == 0.0 || norm_b == 0.0 {
        0.0
    } else {
        dot_product / (norm_a * norm_b)
    }
}

// (already re-exported at the top)

#[cfg(test)]
mod tests {
    use super::*;
    use crate::memory::redis_store::InMemoryEmbeddingCache;
    use crate::agent::{HashEmbeddingAgent, LengthRerankAgent};

    #[tokio::test]
    async fn test_cache_key_generation() {
        let key1 = cache_key("test content");
        let key2 = cache_key("test content");
        let key3 = cache_key("different content");

        assert_eq!(key1, key2); // Same content should produce same key
        assert_ne!(key1, key3); // Different content should produce different keys
        assert!(key1.starts_with("embedding:"));
    }

    #[tokio::test]
    async fn test_cosine_similarity() {
        let a = vec![1.0, 0.0, 0.0];
        let b = vec![1.0, 0.0, 0.0];
        let c = vec![0.0, 1.0, 0.0];

        assert!((cosine(&a, &b) - 1.0).abs() < 1e-6); // Identical vectors
        assert!((cosine(&a, &c) - 0.0).abs() < 1e-6); // Orthogonal vectors

        // Test with different lengths
        let d = vec![1.0, 0.0];
        assert_eq!(cosine(&a, &d), 0.0);

        // Test with empty vectors
        let e = vec![];
        assert_eq!(cosine(&a, &e), 0.0);
    }

    #[tokio::test]
    async fn test_memory_kv_operations() {
        let cache = Arc::new(InMemoryEmbeddingCache::new());
        let embed = Arc::new(HashEmbeddingAgent::new(384));
        let rerank = Arc::new(LengthRerankAgent::new());
        let memory = Memory::new(embed, rerank, cache);

        // Test set and get
        let key = "test_key";
        let value = serde_json::json!({"data": "test_value"});

        memory.set_kv(key, value.clone()).await.unwrap();
        let retrieved = memory.get_kv(key).await.unwrap();

        assert_eq!(retrieved, Some(value));

        // Test non-existent key
        let missing = memory.get_kv("nonexistent").await.unwrap();
        assert_eq!(missing, None);
    }

    #[tokio::test]
    async fn test_memory_stats() {
        let cache = Arc::new(InMemoryEmbeddingCache::new());
        let embed = Arc::new(HashEmbeddingAgent::new(384));
        let rerank = Arc::new(LengthRerankAgent::new());
        let memory = Memory::new(embed, rerank, cache)
            .with_max_fragments(100);

        let stats = memory.stats().await;
        assert_eq!(stats.total_fragments, 0);
        assert_eq!(stats.embedding_dim, 384);
    }

    #[tokio::test]
    async fn test_memory_clear() {
        let cache = Arc::new(InMemoryEmbeddingCache::new());
        let embed = Arc::new(HashEmbeddingAgent::new(384));
        let rerank = Arc::new(LengthRerankAgent::new());
        let memory = Memory::new(embed, rerank, cache);

        // Add some data
        memory.set_kv("key1", serde_json::json!("value1")).await.unwrap();
        memory.set_kv("key2", serde_json::json!("value2")).await.unwrap();

        // Clear everything
        memory.clear().await.unwrap();

        // Verify everything is cleared
        let stats = memory.stats().await;
        assert_eq!(stats.total_fragments, 0);

        assert_eq!(memory.get_kv("key1").await.unwrap(), None);
        assert_eq!(memory.get_kv("key2").await.unwrap(), None);
    }
}

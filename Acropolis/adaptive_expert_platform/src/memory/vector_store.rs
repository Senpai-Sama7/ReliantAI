//! Advanced vector memory store with HNSW indexing for semantic search

use anyhow::{anyhow, Result};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use uuid::Uuid;
use serde::{Deserialize, Serialize};
use dashmap::DashMap;
use lru::LruCache;
use parking_lot::Mutex;
use tracing::{info, warn, error, instrument};

#[cfg(feature = "with-vector-search")]
use hnsw_rs::prelude::*;

/// Memory fragment with vector embedding
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MemoryFragment {
    pub id: Uuid,
    pub content: String,
    pub embedding: Vec<f32>,
    pub metadata: HashMap<String, serde_json::Value>,
    pub created_at: chrono::DateTime<chrono::Utc>,
    pub updated_at: chrono::DateTime<chrono::Utc>,
    pub access_count: u64,
}

impl MemoryFragment {
    pub fn new(content: String, embedding: Vec<f32>) -> Self {
        let now = chrono::Utc::now();
        Self {
            id: Uuid::new_v4(),
            content,
            embedding,
            metadata: HashMap::new(),
            created_at: now,
            updated_at: now,
            access_count: 0,
        }
    }

    pub fn with_metadata(mut self, key: String, value: serde_json::Value) -> Self {
        self.metadata.insert(key, value);
        self
    }

    pub fn access(&mut self) {
        self.access_count += 1;
        self.updated_at = chrono::Utc::now();
    }
}

/// Configuration for vector store
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct VectorStoreConfig {
    pub max_fragments: usize,
    pub embedding_dim: usize,
    pub similarity_threshold: f32,
    pub hnsw_max_connections: usize,
    pub hnsw_ef_construction: usize,
    pub hnsw_ef_search: usize,
    pub cache_size: usize,
    pub enable_persistence: bool,
    pub persistence_interval_secs: u64,
}

impl Default for VectorStoreConfig {
    fn default() -> Self {
        Self {
            max_fragments: 100_000,
            embedding_dim: 384,
            similarity_threshold: 0.7,
            hnsw_max_connections: 16,
            hnsw_ef_construction: 200,
            hnsw_ef_search: 100,
            cache_size: 10_000,
            enable_persistence: true,
            persistence_interval_secs: 300, // 5 minutes
        }
    }
}

/// Advanced vector store with HNSW indexing
pub struct VectorStore {
    config: VectorStoreConfig,
    fragments: DashMap<Uuid, MemoryFragment>,
    
    #[cfg(feature = "with-vector-search")]
    hnsw_index: Arc<RwLock<Option<Hnsw<f32, DistCosine>>>>,
    
    #[cfg(not(feature = "with-vector-search"))]
    _phantom: std::marker::PhantomData<()>,
    
    similarity_cache: Arc<Mutex<LruCache<String, Vec<(Uuid, f32)>>>>,
    stats: Arc<RwLock<VectorStoreStats>>,
}

#[derive(Debug, Default, Serialize)]
pub struct VectorStoreStats {
    pub total_fragments: usize,
    pub total_searches: u64,
    pub cache_hits: u64,
    pub cache_misses: u64,
    pub average_search_time_ms: f64,
    pub index_build_time_ms: u64,
}

impl VectorStore {
    /// Create a new vector store with configuration
    pub fn new(config: VectorStoreConfig) -> Self {
        let similarity_cache = Arc::new(Mutex::new(LruCache::new(
            std::num::NonZeroUsize::new(config.cache_size).unwrap()
        )));

        Self {
            config,
            fragments: DashMap::new(),
            
            #[cfg(feature = "with-vector-search")]
            hnsw_index: Arc::new(RwLock::new(None)),
            
            #[cfg(not(feature = "with-vector-search"))]
            _phantom: std::marker::PhantomData,
            
            similarity_cache,
            stats: Arc::new(RwLock::new(VectorStoreStats::default())),
        }
    }

    /// Add a memory fragment to the store
    #[instrument(skip(self, fragment))]
    pub async fn add_fragment(&self, mut fragment: MemoryFragment) -> Result<Uuid> {
        // Validate embedding dimension
        if fragment.embedding.len() != self.config.embedding_dim {
            return Err(anyhow!(
                "Embedding dimension mismatch: expected {}, got {}",
                self.config.embedding_dim,
                fragment.embedding.len()
            ));
        }

        // Check if we're at capacity
        if self.fragments.len() >= self.config.max_fragments {
            self.evict_oldest_fragment().await?;
        }

        let id = fragment.id;
        self.fragments.insert(id, fragment);

        // Rebuild HNSW index if needed
        #[cfg(feature = "with-vector-search")]
        self.rebuild_index_if_needed().await?;

        // Update stats
        let mut stats = self.stats.write().await;
        stats.total_fragments = self.fragments.len();

        info!("Added memory fragment {} to vector store", id);
        Ok(id)
    }

    /// Search for similar fragments using vector similarity
    #[instrument(skip(self, query_embedding))]
    pub async fn search_similar(
        &self,
        query_embedding: &[f32],
        top_k: usize,
        min_similarity: Option<f32>,
    ) -> Result<Vec<(MemoryFragment, f32)>> {
        let start_time = std::time::Instant::now();
        
        // Update search stats
        let mut stats = self.stats.write().await;
        stats.total_searches += 1;
        drop(stats);

        // Validate query embedding
        if query_embedding.len() != self.config.embedding_dim {
            return Err(anyhow!(
                "Query embedding dimension mismatch: expected {}, got {}",
                self.config.embedding_dim,
                query_embedding.len()
            ));
        }

        // Check cache first
        let cache_key = format!("{:?}_{}", query_embedding, top_k);
        if let Some(cached_results) = self.similarity_cache.lock().get(&cache_key) {
            let mut stats = self.stats.write().await;
            stats.cache_hits += 1;
            drop(stats);

            let results = self.build_search_results(cached_results, min_similarity).await?;
            return Ok(results);
        }

        // Perform search
        let similar_fragments = if cfg!(feature = "with-vector-search") {
            #[cfg(feature = "with-vector-search")]
            {
                self.hnsw_search(query_embedding, top_k).await?
            }
            #[cfg(not(feature = "with-vector-search"))]
            {
                self.brute_force_search(query_embedding, top_k).await?
            }
        } else {
            self.brute_force_search(query_embedding, top_k).await?
        };

        // Cache results
        self.similarity_cache.lock().put(cache_key, similar_fragments.clone());

        // Update cache miss stats
        let mut stats = self.stats.write().await;
        stats.cache_misses += 1;
        stats.average_search_time_ms = 
            (stats.average_search_time_ms + start_time.elapsed().as_millis() as f64) / 2.0;

        let results = self.build_search_results(&similar_fragments, min_similarity).await?;
        Ok(results)
    }

    /// HNSW-based vector search (when feature enabled)
    #[cfg(feature = "with-vector-search")]
    async fn hnsw_search(&self, query: &[f32], top_k: usize) -> Result<Vec<(Uuid, f32)>> {
        let index_guard = self.hnsw_index.read().await;
        
        if let Some(ref index) = *index_guard {
            let search_results = index.search(query, top_k, self.config.hnsw_ef_search);
            
            let mut results = Vec::new();
            for result in search_results {
                // Map index ID back to fragment UUID
                if let Some(fragment_id) = self.get_fragment_id_by_index(result.d_id).await {
                    results.push((fragment_id, result.distance));
                }
            }
            
            Ok(results)
        } else {
            // Fallback to brute force if index not built
            self.brute_force_search(query, top_k).await
        }
    }

    /// Brute force cosine similarity search (fallback)
    async fn brute_force_search(&self, query: &[f32], top_k: usize) -> Result<Vec<(Uuid, f32)>> {
        use rayon::prelude::*;
        
        let fragments: Vec<_> = self.fragments.iter().collect();
        
        let mut similarities: Vec<(Uuid, f32)> = fragments
            .par_iter()
            .map(|entry| {
                let fragment = entry.value();
                let similarity = cosine_similarity(query, &fragment.embedding);
                (fragment.id, similarity)
            })
            .collect();

        // Sort by similarity (descending)
        similarities.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap_or(std::cmp::Ordering::Equal));
        
        // Take top-k results
        similarities.truncate(top_k);
        
        Ok(similarities)
    }

    /// Build final search results with metadata
    async fn build_search_results(
        &self,
        similar_fragments: &[(Uuid, f32)],
        min_similarity: Option<f32>,
    ) -> Result<Vec<(MemoryFragment, f32)>> {
        let threshold = min_similarity.unwrap_or(self.config.similarity_threshold);
        
        let mut results = Vec::new();
        for (fragment_id, similarity) in similar_fragments {
            if *similarity >= threshold {
                if let Some(mut fragment) = self.fragments.get_mut(fragment_id) {
                    fragment.access(); // Update access statistics
                    results.push((fragment.clone(), *similarity));
                }
            }
        }
        
        Ok(results)
    }

    /// Rebuild HNSW index when needed
    #[cfg(feature = "with-vector-search")]
    async fn rebuild_index_if_needed(&self) -> Result<()> {
        // Rebuild every 1000 fragments or if index doesn't exist
        if self.fragments.len() % 1000 == 0 || self.hnsw_index.read().await.is_none() {
            self.rebuild_hnsw_index().await?;
        }
        Ok(())
    }

    /// Rebuild the HNSW index from scratch
    #[cfg(feature = "with-vector-search")]
    async fn rebuild_hnsw_index(&self) -> Result<()> {
        let start_time = std::time::Instant::now();
        info!("Rebuilding HNSW index for {} fragments", self.fragments.len());

        let mut index = Hnsw::<f32, DistCosine>::new(
            self.config.hnsw_max_connections,
            self.fragments.len(),
            16,
            self.config.hnsw_ef_construction,
            DistCosine {},
        );

        // Add all fragments to the index
        let mut fragment_id_map = HashMap::new();
        for (idx, entry) in self.fragments.iter().enumerate() {
            let fragment = entry.value();
            index.insert((&fragment.embedding, idx));
            fragment_id_map.insert(idx, fragment.id);
        }

        // Store the rebuilt index
        let mut index_guard = self.hnsw_index.write().await;
        *index_guard = Some(index);

        // Update build time stats
        let mut stats = self.stats.write().await;
        stats.index_build_time_ms = start_time.elapsed().as_millis() as u64;

        info!("HNSW index rebuilt in {}ms", stats.index_build_time_ms);
        Ok(())
    }

    /// Map HNSW index ID back to fragment UUID
    #[cfg(feature = "with-vector-search")]
    async fn get_fragment_id_by_index(&self, index_id: usize) -> Option<Uuid> {
        // This is a simplified mapping - in production you'd maintain a proper ID mapping
        self.fragments.iter().nth(index_id).map(|entry| entry.value().id)
    }

    /// Evict oldest fragment when at capacity
    async fn evict_oldest_fragment(&self) -> Result<()> {
        // Find oldest fragment by creation time
        let oldest_id = self.fragments
            .iter()
            .min_by_key(|entry| entry.value().created_at)
            .map(|entry| entry.value().id);

        if let Some(id) = oldest_id {
            self.fragments.remove(&id);
            warn!("Evicted oldest memory fragment {} due to capacity limit", id);
        }

        Ok(())
    }

    /// Get fragment by ID
    pub async fn get_fragment(&self, id: &Uuid) -> Option<MemoryFragment> {
        self.fragments.get(id).map(|entry| {
            let mut fragment = entry.value().clone();
            fragment.access();
            fragment
        })
    }

    /// Remove fragment by ID
    pub async fn remove_fragment(&self, id: &Uuid) -> Result<bool> {
        let removed = self.fragments.remove(id).is_some();
        
        if removed {
            // Clear cache since index changed
            self.similarity_cache.lock().clear();
            
            // Update stats
            let mut stats = self.stats.write().await;
            stats.total_fragments = self.fragments.len();
        }
        
        Ok(removed)
    }

    /// Get store statistics
    pub async fn get_stats(&self) -> VectorStoreStats {
        let mut stats = self.stats.read().await.clone();
        stats.total_fragments = self.fragments.len();
        stats
    }

    /// Clear all fragments
    pub async fn clear(&self) -> Result<()> {
        self.fragments.clear();
        self.similarity_cache.lock().clear();
        
        #[cfg(feature = "with-vector-search")]
        {
            let mut index_guard = self.hnsw_index.write().await;
            *index_guard = None;
        }
        
        let mut stats = self.stats.write().await;
        *stats = VectorStoreStats::default();
        
        info!("Cleared all fragments from vector store");
        Ok(())
    }
}

/// Calculate cosine similarity between two vectors
fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    if a.len() != b.len() {
        return 0.0;
    }

    let dot_product: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let norm_a: f32 = a.iter().map(|x| x * x).sum::<f32>().sqrt();
    let norm_b: f32 = b.iter().map(|x| x * x).sum::<f32>().sqrt();

    if norm_a == 0.0 || norm_b == 0.0 {
        return 0.0;
    }

    dot_product / (norm_a * norm_b)
}
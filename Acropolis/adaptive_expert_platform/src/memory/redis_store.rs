// ===== adaptive_expert_platform/src/memory/redis_store.rs =====
/*!
Embedding-cache back-ends with enhanced security and monitoring:

* **InMemoryEmbeddingCache** – in-process HashMap (good for dev/testing).
* **LruCache** – in-process LRU (good for prod single-instance).
* **RedisCache** – shared cluster cache (prod/horiz-scale).
*/
use anyhow::{Result, anyhow};
use async_trait::async_trait;
use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use tracing::{info, debug, instrument};

#[cfg(feature = "with-redis")]
use {
    redis::{AsyncCommands, RedisResult},
    bb8::{Pool, PooledConnection},
    bb8_redis::RedisConnectionManager,
};

/// Cache trait for embedding storage with enhanced features.
#[async_trait]
pub trait EmbeddingCache: Send + Sync + std::fmt::Debug {
    /// Retrieve embedding vector by key
    async fn get(&self, key: &str) -> Result<Option<Vec<f32>>>;

    /// Store embedding vector with key
    async fn set(&self, key: &str, val: &[f32]) -> Result<()>;

    /// Delete embedding by key
    async fn delete(&self, key: &str) -> Result<()>;

    /// Clear all embeddings (for testing)
    async fn clear(&self) -> Result<()>;

    /// Get cache statistics
    async fn stats(&self) -> Result<CacheStats>;
}

/// Cache statistics for monitoring
#[derive(Debug, Clone)]
pub struct CacheStats {
    pub hits: u64,
    pub misses: u64,
    pub entries: usize,
    pub memory_usage_bytes: usize,
}

/// Simple in-memory cache for development and testing
#[derive(Debug)]
pub struct InMemoryEmbeddingCache {
    storage: Arc<RwLock<HashMap<String, Vec<f32>>>>,
    stats: Arc<RwLock<CacheStats>>,
}

impl InMemoryEmbeddingCache {
    pub fn new() -> Self {
        Self {
            storage: Arc::new(RwLock::new(HashMap::new())),
            stats: Arc::new(RwLock::new(CacheStats {
                hits: 0,
                misses: 0,
                entries: 0,
                memory_usage_bytes: 0,
            })),
        }
    }
}

#[async_trait]
impl EmbeddingCache for InMemoryEmbeddingCache {
    #[instrument(skip(self))]
    async fn get(&self, key: &str) -> Result<Option<Vec<f32>>> {
        debug!("Getting embedding for key: {}", key);

        let storage = self.storage.read()
            .map_err(|e| anyhow!("Failed to acquire read lock: {}", e))?;

        let result = storage.get(key).cloned();

        // Update statistics
        {
            let mut stats = self.stats.write()
                .map_err(|e| anyhow!("Failed to acquire stats write lock: {}", e))?;

            if result.is_some() {
                stats.hits += 1;
            } else {
                stats.misses += 1;
            }
        }

        Ok(result)
    }

    #[instrument(skip(self, val))]
    async fn set(&self, key: &str, val: &[f32]) -> Result<()> {
        debug!("Setting embedding for key: {} (size: {})", key, val.len());

        let mut storage = self.storage.write()
            .map_err(|e| anyhow!("Failed to acquire write lock: {}", e))?;

        let old_size = storage.get(key).map(|v| v.len()).unwrap_or(0);
        storage.insert(key.to_string(), val.to_vec());

        // Update statistics
        {
            let mut stats = self.stats.write()
                .map_err(|e| anyhow!("Failed to acquire stats write lock: {}", e))?;

            stats.entries = storage.len();
            stats.memory_usage_bytes = stats.memory_usage_bytes
                - old_size * std::mem::size_of::<f32>()
                + val.len() * std::mem::size_of::<f32>();
        }

        Ok(())
    }

    #[instrument(skip(self))]
    async fn delete(&self, key: &str) -> Result<()> {
        debug!("Deleting embedding for key: {}", key);

        let mut storage = self.storage.write()
            .map_err(|e| anyhow!("Failed to acquire write lock: {}", e))?;

        if let Some(removed) = storage.remove(key) {
            let mut stats = self.stats.write()
                .map_err(|e| anyhow!("Failed to acquire stats write lock: {}", e))?;

            stats.entries = storage.len();
            stats.memory_usage_bytes -= removed.len() * std::mem::size_of::<f32>();
        }

        Ok(())
    }

    async fn clear(&self) -> Result<()> {
        info!("Clearing all embeddings from cache");

        let mut storage = self.storage.write()
            .map_err(|e| anyhow!("Failed to acquire write lock: {}", e))?;

        storage.clear();

        let mut stats = self.stats.write()
            .map_err(|e| anyhow!("Failed to acquire stats write lock: {}", e))?;

        *stats = CacheStats {
            hits: 0,
            misses: 0,
            entries: 0,
            memory_usage_bytes: 0,
        };

        Ok(())
    }

    async fn stats(&self) -> Result<CacheStats> {
        let stats = self.stats.read()
            .map_err(|e| anyhow!("Failed to acquire stats read lock: {}", e))?;

        Ok(stats.clone())
    }
}

/// LRU cache implementation (when lru crate is available)

pub struct LruCache {
    inner: Arc<RwLock<lru::LruCache<String, Vec<f32>>>>,
    stats: Arc<RwLock<CacheStats>>,
}


impl LruCache {
    pub fn new(capacity: usize) -> Self {
        use std::num::NonZeroUsize;
        let cap = NonZeroUsize::new(capacity).unwrap_or(NonZeroUsize::new(1000).unwrap());

        Self {
            inner: Arc::new(RwLock::new(lru::LruCache::new(cap))),
            stats: Arc::new(RwLock::new(CacheStats {
                hits: 0,
                misses: 0,
                entries: 0,
                memory_usage_bytes: 0,
            })),
        }
    }
}


impl std::fmt::Debug for LruCache {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("LruCache")
            .field("capacity", &self.inner.read().unwrap().cap())
            .finish()
    }
}


#[async_trait]
impl EmbeddingCache for LruCache {
    async fn get(&self, key: &str) -> Result<Option<Vec<f32>>> {
        let mut cache = self.inner.write()
            .map_err(|e| anyhow!("Failed to acquire write lock: {}", e))?;

        let result = cache.get(key).cloned();

        let mut stats = self.stats.write()
            .map_err(|e| anyhow!("Failed to acquire stats write lock: {}", e))?;

        if result.is_some() {
            stats.hits += 1;
        } else {
            stats.misses += 1;
        }

        Ok(result)
    }

    async fn set(&self, key: &str, val: &[f32]) -> Result<()> {
        let mut cache = self.inner.write()
            .map_err(|e| anyhow!("Failed to acquire write lock: {}", e))?;

        cache.put(key.to_string(), val.to_vec());

        let mut stats = self.stats.write()
            .map_err(|e| anyhow!("Failed to acquire stats write lock: {}", e))?;

        stats.entries = cache.len();
        stats.memory_usage_bytes = cache.len() * val.len() * std::mem::size_of::<f32>();

        Ok(())
    }

    async fn delete(&self, key: &str) -> Result<()> {
        let mut cache = self.inner.write()
            .map_err(|e| anyhow!("Failed to acquire write lock: {}", e))?;

        cache.pop(key);
        Ok(())
    }

    async fn clear(&self) -> Result<()> {
        let mut cache = self.inner.write()
            .map_err(|e| anyhow!("Failed to acquire write lock: {}", e))?;

        cache.clear();

        let mut stats = self.stats.write()
            .map_err(|e| anyhow!("Failed to acquire stats write lock: {}", e))?;

        *stats = CacheStats {
            hits: 0,
            misses: 0,
            entries: 0,
            memory_usage_bytes: 0,
        };

        Ok(())
    }

    async fn stats(&self) -> Result<CacheStats> {
        let stats = self.stats.read()
            .map_err(|e| anyhow!("Failed to acquire stats read lock: {}", e))?;

        Ok(stats.clone())
    }
}

/// Redis distributed cache for production use
#[cfg(feature = "with-redis")]
#[derive(Debug)]
pub struct RedisCache {
    pool: Pool<RedisConnectionManager>,
    stats: Arc<RwLock<CacheStats>>,
    key_prefix: String,
}

#[cfg(feature = "with-redis")]
impl RedisCache {
    pub async fn new(redis_url: &str) -> Result<Self> {
        let manager = RedisConnectionManager::new(redis_url)?;
        let pool = Pool::builder()
            .max_size(10)
            .build(manager)
            .await?;

        // Test connection
        let _conn = pool.get().await
            .map_err(|e| anyhow!("Failed to connect to Redis: {}", e))?;

        info!("Connected to Redis at {}", redis_url);

        Ok(Self {
            pool,
            stats: Arc::new(RwLock::new(CacheStats {
                hits: 0,
                misses: 0,
                entries: 0,
                memory_usage_bytes: 0,
            })),
            key_prefix: "aep:embeddings:".to_string(),
        })
    }

    fn make_key(&self, key: &str) -> String {
        format!("{}{}", self.key_prefix, key)
    }
}

#[cfg(feature = "with-redis")]
#[async_trait]
impl EmbeddingCache for RedisCache {
    #[instrument(skip(self))]
    async fn get(&self, key: &str) -> Result<Option<Vec<f32>>> {
        let mut conn = self.pool.get().await
            .map_err(|e| anyhow!("Failed to get Redis connection: {}", e))?;

        let redis_key = self.make_key(key);
        let result: RedisResult<Vec<u8>> = conn.get(&redis_key).await;

        let mut stats = self.stats.write()
            .map_err(|e| anyhow!("Failed to acquire stats write lock: {}", e))?;

        match result {
            Ok(bytes) => {
                stats.hits += 1;
                // Deserialize Vec<f32> from bytes
                let floats = bincode::deserialize(&bytes)
                    .map_err(|e| anyhow!("Failed to deserialize embedding: {}", e))?;
                Ok(Some(floats))
            }
            Err(redis::RedisError { kind: redis::ErrorKind::TypeError, .. }) => {
                stats.misses += 1;
                Ok(None)
            }
            Err(e) => {
                error!("Redis error: {}", e);
                Err(anyhow!("Redis error: {}", e))
            }
        }
    }

    #[instrument(skip(self, val))]
    async fn set(&self, key: &str, val: &[f32]) -> Result<()> {
        let mut conn = self.pool.get().await
            .map_err(|e| anyhow!("Failed to get Redis connection: {}", e))?;

        let redis_key = self.make_key(key);
        let bytes = bincode::serialize(val)
            .map_err(|e| anyhow!("Failed to serialize embedding: {}", e))?;

        let _: () = conn.set_ex(&redis_key, bytes, 86400).await // 24 hour TTL
            .map_err(|e| anyhow!("Failed to set Redis key: {}", e))?;

        Ok(())
    }

    async fn delete(&self, key: &str) -> Result<()> {
        let mut conn = self.pool.get().await
            .map_err(|e| anyhow!("Failed to get Redis connection: {}", e))?;

        let redis_key = self.make_key(key);
        let _: () = conn.del(&redis_key).await
            .map_err(|e| anyhow!("Failed to delete Redis key: {}", e))?;

        Ok(())
    }

    async fn clear(&self) -> Result<()> {
        let mut conn = self.pool.get().await
            .map_err(|e| anyhow!("Failed to get Redis connection: {}", e))?;

        // Use SCAN to find all keys with our prefix
        let pattern = format!("{}*", self.key_prefix);
        let keys: Vec<String> = redis::cmd("SCAN")
            .arg(0)
            .arg("MATCH")
            .arg(&pattern)
            .arg("COUNT")
            .arg(1000)
            .query_async(&mut *conn)
            .await
            .map_err(|e| anyhow!("Failed to scan Redis keys: {}", e))?;

        if !keys.is_empty() {
            let _: () = conn.del(&keys).await
                .map_err(|e| anyhow!("Failed to delete Redis keys: {}", e))?;
        }

        Ok(())
    }

    async fn stats(&self) -> Result<CacheStats> {
        let stats = self.stats.read()
            .map_err(|e| anyhow!("Failed to acquire stats read lock: {}", e))?;

        Ok(stats.clone())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_in_memory_cache() {
        let cache = InMemoryEmbeddingCache::new();

        // Test set and get
        let key = "test_key";
        let embedding = vec![1.0, 2.0, 3.0];

        cache.set(key, &embedding).await.unwrap();
        let retrieved = cache.get(key).await.unwrap();

        assert_eq!(retrieved, Some(embedding));

        // Test miss
        let missing = cache.get("nonexistent").await.unwrap();
        assert_eq!(missing, None);

        // Test stats
        let stats = cache.stats().await.unwrap();
        assert_eq!(stats.hits, 1);
        assert_eq!(stats.misses, 1);
        assert_eq!(stats.entries, 1);

        // Test delete
        cache.delete(key).await.unwrap();
        let deleted = cache.get(key).await.unwrap();
        assert_eq!(deleted, None);

        // Test clear
        cache.set("key1", &[1.0]).await.unwrap();
        cache.set("key2", &[2.0]).await.unwrap();
        cache.clear().await.unwrap();

        let stats = cache.stats().await.unwrap();
        assert_eq!(stats.entries, 0);
    }

    #[tokio::test]
    async fn test_cache_concurrent_access() {
        let cache = Arc::new(InMemoryEmbeddingCache::new());
        let mut handles = Vec::new();

        // Spawn multiple tasks writing to cache
        for i in 0..100 {
            let cache_clone = cache.clone();
            let handle = tokio::spawn(async move {
                let key = format!("key_{}", i);
                let embedding = vec![i as f32; 10];
                cache_clone.set(&key, &embedding).await.unwrap();

                let retrieved = cache_clone.get(&key).await.unwrap();
                assert_eq!(retrieved, Some(embedding));
            });
            handles.push(handle);
        }

        // Wait for all tasks to complete
        for handle in handles {
            handle.await.unwrap();
        }

        let stats = cache.stats().await.unwrap();
        assert_eq!(stats.entries, 100);
        assert_eq!(stats.hits, 100);
    }
}

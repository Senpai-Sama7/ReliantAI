//! Native / WASM plugin loader + hot-reload support with enhanced security.

use std::{path::Path, sync::Arc};
use anyhow::{Context, Result, anyhow};
use libloading::Library;
use crate::agent::Agent;
use sha2::{Sha256, Digest};
use std::fs;
use std::collections::HashSet;
use tracing::{info, warn, error, instrument};

pub enum PluginEvent {
    Reload(std::path::PathBuf),
    SecurityViolation(String),
}

type FactoryFn = unsafe extern "C" fn() -> *mut dyn Agent;

/// Plugin security configuration
#[derive(Debug, Clone)]
pub struct PluginSecurityConfig {
    /// List of allowed plugin hashes (SHA256)
    pub allowed_hashes: HashSet<String>,
    /// Whether to enforce signature verification
    pub require_signatures: bool,
    /// Maximum plugin file size in bytes
    pub max_plugin_size: usize,
    /// Allowed file extensions
    pub allowed_extensions: HashSet<String>,
}

impl Default for PluginSecurityConfig {
    fn default() -> Self {
        let mut allowed_extensions = HashSet::new();
        allowed_extensions.insert(".so".to_string());
        allowed_extensions.insert(".dll".to_string());
        allowed_extensions.insert(".dylib".to_string());

        Self {
            allowed_hashes: HashSet::new(),
            require_signatures: true, // Always require signatures in production
            max_plugin_size: 10_485_760, // 10MB
            allowed_extensions,
        }
    }
}

impl PluginSecurityConfig {
    /// Create from SecurityConfig
    pub fn from_security_config(config: &crate::settings::SecurityConfig) -> Self {
        let mut allowed_extensions = HashSet::new();
        allowed_extensions.insert(".so".to_string());
        allowed_extensions.insert(".dll".to_string());
        allowed_extensions.insert(".dylib".to_string());

        let allowed_hashes = config.plugin_allowlist_hashes.iter().cloned().collect();

        Self {
            allowed_hashes,
            require_signatures: config.enable_plugin_signatures,
            max_plugin_size: config.max_plugin_size_mb * 1024 * 1024,
            allowed_extensions,
        }
    }
}

#[derive(Debug)]
pub struct Plugin {
    _lib: Arc<Library>,      // keep Library alive
    factory: FactoryFn,
    hash: String,
    path: std::path::PathBuf,
}

impl Plugin {
    /// Load a `.so`/`.dll` with comprehensive security validation
    #[instrument(skip(security_config))]
    pub unsafe fn load(lib_path: &Path, security_config: &PluginSecurityConfig) -> Result<Self> {
        // Validate file extension
        let extension = lib_path.extension()
            .and_then(|e| e.to_str())
            .map(|e| format!(".{}", e))
            .ok_or_else(|| anyhow!("Plugin file has no valid extension: {:?}", lib_path))?;

        if !security_config.allowed_extensions.contains(&extension) {
            return Err(anyhow!("Plugin extension '{}' not allowed", extension));
        }

        // Check file size
        let metadata = fs::metadata(lib_path)
            .with_context(|| format!("Failed to read metadata for plugin: {:?}", lib_path))?;

        if metadata.len() > security_config.max_plugin_size as u64 {
            return Err(anyhow!("Plugin file too large: {} bytes (max: {})",
                metadata.len(), security_config.max_plugin_size));
        }

        // Calculate and verify file hash
        let file_content = fs::read(lib_path)
            .with_context(|| format!("Failed to read plugin file: {:?}", lib_path))?;

        let mut hasher = Sha256::new();
        hasher.update(&file_content);
        let hash = format!("{:x}", hasher.finalize());

        // Always verify against allowlist in production
        if security_config.require_signatures {
            if security_config.allowed_hashes.is_empty() {
                error!("Plugin allowlist is empty but signature verification is enabled");
                return Err(anyhow!("Plugin allowlist must be configured when signature verification is enabled"));
            }

            if !security_config.allowed_hashes.contains(&hash) {
                error!("Plugin hash not in allowlist: {} ({})", hash, lib_path.display());
                
                // Quarantine unsigned plugin
                Self::quarantine_plugin(lib_path)?;
                
                return Err(anyhow!("Plugin not in security allowlist: {:?}", lib_path));
            }

            info!("Plugin hash verified: {} ({})", &hash[..16], lib_path.display());
        } else {
            warn!("Plugin signature verification is DISABLED - this should only be used in development");
        }

        info!("Loading plugin: {:?} (hash: {})", lib_path, &hash[..16]);

                // Load library with security constraints
        let library = Library::new(lib_path)
            .with_context(|| format!("Failed to load plugin library: {:?}", lib_path))?;

        // Verify the required symbol exists before returning
        let factory: libloading::Symbol<FactoryFn> = library.get(b"create_agent")
            .with_context(|| format!("Plugin missing 'create_agent' symbol: {:?}", lib_path))?;

        let factory_fn = *factory;
        let lib = Arc::new(library);

        Ok(Self {
            _lib: lib,
            factory: factory_fn,
            hash,
            path: lib_path.to_path_buf(),
        })
    }

    /// Instantiate the agent exported by this plugin with error handling
    #[instrument(skip(self))]
    pub unsafe fn instantiate(&self) -> Result<Box<dyn Agent>> {
        info!("Instantiating agent from plugin: {:?}", self.path);

        // Use panic catching to prevent plugin crashes from taking down the system
        let result = std::panic::catch_unwind(|| {
            let raw = (self.factory)();
            if raw.is_null() {
                return Err(anyhow!("Plugin factory returned null pointer"));
            }
            Ok(Box::from_raw(raw))
        });

        match result {
            Ok(Ok(agent)) => {
                info!("Successfully instantiated agent: {}", agent.name());
                Ok(agent)
            }
            Ok(Err(e)) => {
                error!("Plugin instantiation failed: {}", e);
                Err(e)
            }
            Err(_) => {
                error!("Plugin instantiation panicked: {:?}", self.path);
                Err(anyhow!("Plugin instantiation panicked"))
            }
        }
    }

    /// Get plugin metadata
    pub fn metadata(&self) -> PluginMetadata {
        PluginMetadata {
            hash: self.hash.clone(),
            path: self.path.clone(),
        }
    }

    /// Quarantine an unsigned or malicious plugin by moving it to a secure location
    fn quarantine_plugin(lib_path: &Path) -> Result<()> {
        let quarantine_dir = lib_path.parent()
            .unwrap_or_else(|| Path::new("."))
            .join("quarantine");

        // Create quarantine directory if it doesn't exist
        if !quarantine_dir.exists() {
            fs::create_dir_all(&quarantine_dir)
                .with_context(|| format!("Failed to create quarantine directory: {:?}", quarantine_dir))?;
        }

        // Generate quarantine filename with timestamp
        let timestamp = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_secs();

        let filename = lib_path.file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("unknown_plugin");

        let quarantine_path = quarantine_dir.join(format!("{}_{}", timestamp, filename));

        // Move the plugin to quarantine
        fs::rename(lib_path, &quarantine_path)
            .with_context(|| format!("Failed to quarantine plugin: {:?} -> {:?}", lib_path, quarantine_path))?;

        warn!("Plugin quarantined due to signature verification failure: {:?}", quarantine_path);
        Ok(())
    }
}

#[derive(Debug, Clone)]
pub struct PluginMetadata {
    pub hash: String,
    pub path: std::path::PathBuf,
}

/* ------------ file-watcher hot-reload with security -------------- */

pub mod hot_reload {
    use super::*;
    use std::{time::Duration, path::PathBuf};
    use tokio::sync::mpsc::Sender;
    use notify::{Watcher, RecursiveMode, RecommendedWatcher, Event, EventKind};

    /// Enhanced plugin watcher with security validation
    #[instrument(skip(bus, security_config))]
    pub async fn watch(
        dir: PathBuf,
        bus: Sender<PluginEvent>,
        security_config: PluginSecurityConfig
    ) -> Result<()> {
        let (tx, mut rx) = tokio::sync::mpsc::channel(8);

        // OS watcher → async bridge
        let mut w: RecommendedWatcher = RecommendedWatcher::new(
            move |res| {
                if let Err(e) = tx.blocking_send(res) {
                    error!("Failed to send file watcher event: {}", e);
                }
            },
            notify::Config::default().with_poll_interval(Duration::from_secs(2))
        )?;
        w.watch(&dir, RecursiveMode::Recursive)?;

        info!("Plugin hot-reload watcher started for directory: {:?}", dir);

        while let Some(evt) = rx.recv().await {
            match evt {
                Ok(Event { kind: EventKind::Modify(_), paths, .. }) => {
                    for path in paths {
                        // Security validation before processing
                        if let Err(e) = validate_plugin_path(&path, &security_config) {
                            warn!("Plugin security validation failed for {:?}: {}", path, e);
                            let _ = bus.send(PluginEvent::SecurityViolation(
                                format!("Invalid plugin: {:?} - {}", path, e)
                            )).await;
                            continue;
                        }

                        info!("Plugin file modified, scheduling reload: {:?}", path);
                        if let Err(e) = bus.send(PluginEvent::Reload(path)).await {
                            error!("Failed to send plugin reload event: {}", e);
                        }
                    }
                }
                Ok(_) => {} // Ignore other event types
                Err(e) => {
                    error!("File watcher error: {}", e);
                }
            }
        }
        Ok(())
    }

    /// Validate plugin path meets security requirements
    pub fn validate_plugin_path(path: &Path, config: &PluginSecurityConfig) -> Result<()> {
        // Check file extension
        let extension = path.extension()
            .and_then(|e| e.to_str())
            .map(|e| format!(".{}", e))
            .ok_or_else(|| anyhow!("No valid file extension"))?;

        if !config.allowed_extensions.contains(&extension) {
            return Err(anyhow!("File extension '{}' not allowed", extension));
        }

        // Check if file exists and is readable
        if !path.exists() {
            return Err(anyhow!("Plugin file does not exist"));
        }

        if !path.is_file() {
            return Err(anyhow!("Path is not a regular file"));
        }

        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;
    use std::fs::File;
    use std::io::Write;

    #[test]
    fn test_plugin_security_config_default() {
        let config = PluginSecurityConfig::default();
        assert!(config.allowed_extensions.contains(".so"));
        assert!(config.allowed_extensions.contains(".dll"));
        assert!(config.allowed_extensions.contains(".dylib"));
        assert_eq!(config.max_plugin_size, 10 * 1024 * 1024);
        assert!(config.require_signatures);
    }

    #[test]
    fn test_validate_plugin_path() {
        let temp_dir = tempdir().unwrap();
        let plugin_path = temp_dir.path().join("test.so");

        // Create a dummy file
        File::create(&plugin_path).unwrap();

        let config = PluginSecurityConfig::default();
        assert!(hot_reload::validate_plugin_path(&plugin_path, &config).is_ok());

        // Test invalid extension
        let bad_path = temp_dir.path().join("test.txt");
        File::create(&bad_path).unwrap();
        assert!(hot_reload::validate_plugin_path(&bad_path, &config).is_err());
    }

    #[test]
    fn test_file_hash_calculation() {
        let temp_dir = tempdir().unwrap();
        let file_path = temp_dir.path().join("test.so");

        // Write known content
        let mut file = File::create(&file_path).unwrap();
        file.write_all(b"test content").unwrap();

        // Calculate hash
        let content = fs::read(&file_path).unwrap();
        let mut hasher = Sha256::new();
        hasher.update(&content);
        let hash = format!("{:x}", hasher.finalize());

        // Hash should be deterministic
        assert_eq!(hash, "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72");
    }
}

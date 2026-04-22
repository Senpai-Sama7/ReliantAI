//! WebAssembly plugin support using the Wasmtime runtime.
//!
//! This module is compiled when the `wasm` feature is enabled.  It
//! provides a simple manager for loading WebAssembly components from
//! the plugin directory and instantiating them using Wasmtime.  The
//! WebAssembly component model allows Wasm modules to interact with
//! their host via functions defined in a WIT (WebAssembly Interface
//! Types) definition.  See the Wasmtime documentation and the
//! blog post “Making a plugin system in Rust using Wasmtime and WIT”
//! for a high-level discussion of using Wasm components as plugins
//!【826651234273768†L31-L40】.
//!
//! At this time the interface is intentionally minimal: plugins are
//! expected to export a function named `run` that takes no
//! parameters and returns no result.  When a plugin is loaded the
//! orchestrator calls its `run` function once.  More advanced
//! interactions (e.g. passing data back and forth or implementing
//! custom interfaces) can be added by extending this manager.

#[cfg(feature = "wasm")]
use anyhow::{anyhow, Result};
#[cfg(feature = "wasm")]
use once_cell::sync::Lazy;
#[cfg(feature = "wasm")]
use wasmtime::{component::Component, Config, Engine, Store};
#[cfg(feature = "wasm")]
use wasmtime::component::{Instance, Linker, TypedFunc};
#[cfg(feature = "wasm")]
use std::path::Path;

/// The global Wasmtime engine used for all Wasm components.  We
/// initialize it with the component model and parallel compilation
/// enabled.  Lazy initialization ensures the engine is created on
/// first use.  See the blog post referenced above for details【826651234273768†L31-L40】.
#[cfg(feature = "wasm")]
static ENGINE: Lazy<Engine> = Lazy::new(|| {
    let mut config = Config::default();
    config.wasm_component_model(true);
    config.parallel_compilation(true);
    Engine::new(&config).expect("Failed to create Wasmtime engine")
});

/// Manager responsible for loading Wasm component plugins.
#[cfg(feature = "wasm")]
pub struct WasmPluginManager;

#[cfg(feature = "wasm")]
impl WasmPluginManager {
    /// Load a WebAssembly component from the given file path and call
    /// its `run` function.  The component must define a `run`
    /// exported function with signature `() -> ()`.  Any errors
    /// encountered during loading or execution are returned.
    pub async fn load_and_run<P: AsRef<Path>>(path: P) -> Result<()> {
        let path = path.as_ref();
        let component = Component::from_file(&*ENGINE, path)
            .map_err(|e| anyhow!("Failed to compile Wasm component {}: {}", path.display(), e))?;
        let mut linker: Linker<()> = Linker::new(&*ENGINE);
        let mut store: Store<()> = Store::new(&*ENGINE, ());
        // Instantiate the component.  Because we don't define any
        // imports the host side has no functions to expose.
        let (instance, _) = Instance::new_async(&mut store, &component, &linker)
            .await
            .map_err(|e| anyhow!("Failed to instantiate Wasm component {}: {}", path.display(), e))?;
        // Expect an exported `run` function with no parameters.  If
        // present call it immediately.  Note that invoking the
        // function is async because Wasmtime may need to perform
        // asynchronous host calls.
        let run_func: TypedFunc<(), ()> = instance
            .get_typed_func(&mut store, "run")
            .map_err(|e| anyhow!("Wasm component {} does not export 'run': {}", path.display(), e))?;
        run_func
            .call_async(&mut store, ())
            .await
            .map_err(|e| anyhow!("Error calling 'run' in {}: {}", path.display(), e))?;
        Ok(())
    }
}
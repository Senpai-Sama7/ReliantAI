#!/usr/bin/env python3
"""
Integration tests for Enterprise Backup System
Tests the complete backup workflow end-to-end
"""

import pytest
import tempfile
import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
import shutil
import time

# Import system components
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from core.config_manager import EnterpriseConfigManager
from monitoring.enterprise_monitoring import EnterpriseMonitoring

@pytest.mark.asyncio
class TestBackupSystemIntegration:
    """Integration tests for complete backup system"""

    @pytest.fixture
    async def temp_environment(self):
        """Create temporary test environment"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create directory structure
            source_dir = temp_path / "source"
            dest_dir = temp_path / "destination"
            config_dir = temp_path / "config"

            source_dir.mkdir()
            dest_dir.mkdir()
            config_dir.mkdir()
            (config_dir / "environments").mkdir()
            (config_dir / "schemas").mkdir()

            # Create test files
            test_files = {
                "document.txt": "This is a test document.",
                "code.py": "print('Hello, world!')",
                "data.json": '{"test": true}',
                "image.png": b"\x89PNG\r\n\x1a\n",  # PNG header
                "large_file.dat": "X" * 1024 * 100  # 100KB file
            }

            for filename, content in test_files.items():
                file_path = source_dir / filename
                if isinstance(content, str):
                    file_path.write_text(content)
                else:
                    file_path.write_bytes(content)

            # Create subdirectories with files
            (source_dir / "subdir1").mkdir()
            (source_dir / "subdir1" / "nested.txt").write_text("Nested file content")

            (source_dir / "subdir2").mkdir()
            (source_dir / "subdir2" / "another.py").write_text("# Another Python file")

            yield {
                "base_dir": temp_path,
                "source_dir": source_dir,
                "dest_dir": dest_dir,
                "config_dir": config_dir,
                "test_files": test_files
            }

    @pytest.fixture
    def integration_config(self, temp_environment):
        """Create integration test configuration"""
        config_data = {
            "version": "1.0.0",
            "backup": {
                "source": {
                    "path": str(temp_environment["source_dir"]),
                    "filters": {
                        "exclude_patterns": ["*.tmp", "*.log"],
                        "max_file_size_mb": 1
                    }
                },
                "destinations": [
                    {
                        "type": "local",
                        "config": {
                            "path": str(temp_environment["dest_dir"])
                        }
                    }
                ],
                "resources": {
                    "max_memory_gb": 1.0,
                    "max_cpu_percent": 50,
                    "concurrent_uploads": 2,
                    "batch_size": 10
                }
            },
            "monitoring": {
                "enabled": True,
                "endpoints": {
                    "health_port": 8081,
                    "metrics_port": 9091
                },
                "logging": {
                    "level": "DEBUG",
                    "format": "json"
                }
            },
            "security": {
                "encryption": {
                    "enabled": False  # Disabled for testing
                },
                "authentication": {
                    "type": "api_key"
                }
            },
            "performance": {
                "circuit_breaker": {
                    "failure_threshold": 2,
                    "timeout_seconds": 5
                },
                "retry_policy": {
                    "max_attempts": 2,
                    "backoff_multiplier": 1.0,
                    "initial_delay_ms": 100
                }
            }
        }

        # Write config file
        config_file = temp_environment["config_dir"] / "environments" / "integration.yml"
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)

        return config_data

    async def test_config_loading_integration(self, temp_environment, integration_config):
        """Test configuration loading with real files"""
        manager = EnterpriseConfigManager(
            config_dir=str(temp_environment["config_dir"]),
            environment="integration"
        )

        # Test loading configuration
        config = manager.load_config()
        assert config["version"] == "1.0.0"
        assert Path(config["backup"]["source"]["path"]) == temp_environment["source_dir"]

        # Test typed configurations
        backup_config = manager.get_backup_config()
        assert backup_config.source_path == str(temp_environment["source_dir"])
        assert backup_config.max_memory_gb == 1.0

        monitoring_config = manager.get_monitoring_config()
        assert monitoring_config.enabled is True
        assert monitoring_config.health_port == 8081

    async def test_monitoring_system_integration(self, integration_config):
        """Test monitoring system initialization and operation"""
        monitoring_config = {
            "service_name": "test-backup-service",
            "metrics_port": 9091,
            "log_level": "DEBUG"
        }

        # Create monitoring instance
        monitoring = EnterpriseMonitoring(monitoring_config)

        # Test initialization
        monitoring.initialize()

        # Test context manager
        async with asyncio.timeout(5):  # Prevent hanging
            with monitoring.operation_context("test_operation", test_id="123") as logger:
                logger.info("Test operation started")

                # Simulate some work
                await asyncio.sleep(0.1)

                # Record metrics
                monitoring.metrics.record_file_processed("success", "text")
                monitoring.metrics.record_file_processed("success", "code")
                monitoring.metrics.record_error("TestError", "low")

        # Test health status
        health_status = monitoring.get_health_status()
        assert "status" in health_status
        assert "timestamp" in health_status
        assert "uptime_seconds" in health_status

    async def test_file_discovery_and_classification(self, temp_environment):
        """Test file discovery and classification workflow"""
        source_dir = temp_environment["source_dir"]

        # Mock semantic analyzer
        class MockSemanticAnalyzer:
            def analyze_file(self, file_path: str):
                file_ext = Path(file_path).suffix.lower()
                if file_ext == ".py":
                    return {
                        "file_type": "source_code",
                        "concepts": ["programming", "python"],
                        "importance": 0.8,
                        "cluster": "development"
                    }
                elif file_ext == ".txt":
                    return {
                        "file_type": "document",
                        "concepts": ["text", "document"],
                        "importance": 0.6,
                        "cluster": "documents"
                    }
                elif file_ext == ".json":
                    return {
                        "file_type": "data",
                        "concepts": ["json", "data"],
                        "importance": 0.7,
                        "cluster": "data"
                    }
                else:
                    return {
                        "file_type": "unknown",
                        "concepts": [],
                        "importance": 0.3,
                        "cluster": "miscellaneous"
                    }

        analyzer = MockSemanticAnalyzer()

        # Discover and classify files
        discovered_files = []
        for file_path in source_dir.rglob("*"):
            if file_path.is_file():
                classification = analyzer.analyze_file(str(file_path))
                discovered_files.append({
                    "path": file_path,
                    "size": file_path.stat().st_size,
                    "classification": classification
                })

        # Verify discoveries
        assert len(discovered_files) >= 5  # At least 5 test files

        # Check specific classifications
        py_files = [f for f in discovered_files if f["path"].suffix == ".py"]
        assert len(py_files) >= 2  # code.py and another.py
        for py_file in py_files:
            assert py_file["classification"]["file_type"] == "source_code"
            assert "python" in py_file["classification"]["concepts"]

    async def test_backup_workflow_simulation(self, temp_environment, integration_config):
        """Test simulated complete backup workflow"""
        source_dir = temp_environment["source_dir"]
        dest_dir = temp_environment["dest_dir"]

        # Mock backup orchestrator behavior
        class MockBackupOrchestrator:
            def __init__(self, config):
                self.config = config
                self.files_processed = []
                self.errors = []

            async def discover_files(self):
                """Discover files in source directory"""
                files = []
                for file_path in source_dir.rglob("*"):
                    if file_path.is_file():
                        files.append({
                            "path": file_path,
                            "size": file_path.stat().st_size,
                            "relative_path": file_path.relative_to(source_dir)
                        })
                return files

            async def process_batch(self, files_batch):
                """Process a batch of files"""
                results = []
                for file_info in files_batch:
                    try:
                        # Simulate file processing
                        await asyncio.sleep(0.01)  # Simulate processing time

                        # Simulate copying file
                        dest_path = dest_dir / file_info["relative_path"]
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(file_info["path"], dest_path)

                        self.files_processed.append(file_info)
                        results.append({"status": "success", "file": file_info})

                    except Exception as e:
                        self.errors.append({"file": file_info, "error": str(e)})
                        results.append({"status": "error", "file": file_info, "error": str(e)})

                return results

            async def run_backup(self):
                """Run complete backup process"""
                start_time = time.time()

                # Discover files
                all_files = await self.discover_files()

                # Process in batches
                batch_size = self.config["backup"]["resources"]["batch_size"]
                for i in range(0, len(all_files), batch_size):
                    batch = all_files[i:i + batch_size]
                    await self.process_batch(batch)

                duration = time.time() - start_time

                return {
                    "duration": duration,
                    "files_discovered": len(all_files),
                    "files_processed": len(self.files_processed),
                    "errors": len(self.errors),
                    "success_rate": len(self.files_processed) / len(all_files) if all_files else 0
                }

        # Run backup simulation
        orchestrator = MockBackupOrchestrator(integration_config)
        result = await orchestrator.run_backup()

        # Verify results
        assert result["files_discovered"] >= 5
        assert result["files_processed"] >= 5
        assert result["success_rate"] >= 0.8  # At least 80% success rate
        assert result["duration"] > 0

        # Verify files were copied
        copied_files = list(dest_dir.rglob("*"))
        copied_files = [f for f in copied_files if f.is_file()]
        assert len(copied_files) >= 5

        # Verify specific files
        assert (dest_dir / "document.txt").exists()
        assert (dest_dir / "code.py").exists()
        assert (dest_dir / "subdir1" / "nested.txt").exists()

    async def test_error_handling_and_recovery(self, temp_environment, integration_config):
        """Test error handling and recovery mechanisms"""

        # Create a mock component that can fail
        class FailingComponent:
            def __init__(self):
                self.failure_count = 0
                self.max_failures = 2

            async def process_file(self, file_path):
                self.failure_count += 1
                if self.failure_count <= self.max_failures:
                    raise Exception(f"Simulated failure {self.failure_count}")
                return {"status": "success", "file": file_path}

        # Test circuit breaker behavior
        component = FailingComponent()

        # Simulate retry logic
        max_retries = integration_config["performance"]["retry_policy"]["max_attempts"]

        success = False
        for attempt in range(max_retries + 1):
            try:
                result = await component.process_file("test.txt")
                success = True
                break
            except Exception as e:
                if attempt < max_retries:
                    await asyncio.sleep(0.1)  # Retry delay
                else:
                    last_error = e

        # Should eventually succeed after retries
        assert success is True

    async def test_resource_monitoring_integration(self, integration_config):
        """Test resource monitoring during operations"""

        # Mock resource monitor
        class MockResourceMonitor:
            def __init__(self):
                self.cpu_usage = 45.0
                self.memory_usage = 60.0
                self.disk_usage = 30.0

            def get_resource_usage(self):
                return {
                    "cpu_percent": self.cpu_usage,
                    "memory_percent": self.memory_usage,
                    "disk_percent": self.disk_usage
                }

            def simulate_load(self):
                """Simulate increasing resource usage"""
                self.cpu_usage = min(90.0, self.cpu_usage + 10)
                self.memory_usage = min(85.0, self.memory_usage + 5)

            def check_thresholds(self, config):
                """Check if usage exceeds thresholds"""
                max_cpu = config["backup"]["resources"]["max_cpu_percent"]
                max_memory_gb = config["backup"]["resources"]["max_memory_gb"]

                # Simulate memory limit (assuming 8GB total system memory)
                max_memory_percent = (max_memory_gb / 8.0) * 100

                return (
                    self.cpu_usage < max_cpu and
                    self.memory_usage < max_memory_percent
                )

        monitor = MockResourceMonitor()

        # Test initial state
        usage = monitor.get_resource_usage()
        assert usage["cpu_percent"] < integration_config["backup"]["resources"]["max_cpu_percent"]

        # Test threshold checking
        assert monitor.check_thresholds(integration_config) is True

        # Simulate high load
        for _ in range(5):
            monitor.simulate_load()

        # Should now exceed thresholds
        assert monitor.check_thresholds(integration_config) is False

    async def test_concurrent_operations(self, temp_environment, integration_config):
        """Test concurrent backup operations"""
        source_dir = temp_environment["source_dir"]

        # Create additional test files for concurrent processing
        for i in range(10):
            (source_dir / f"concurrent_test_{i}.txt").write_text(f"Concurrent test file {i}")

        # Mock concurrent processor
        class ConcurrentProcessor:
            def __init__(self, max_concurrent):
                self.max_concurrent = max_concurrent
                self.active_tasks = 0
                self.completed_tasks = 0
                self.max_active = 0

            async def process_file(self, file_path):
                self.active_tasks += 1
                self.max_active = max(self.max_active, self.active_tasks)

                # Simulate processing time
                await asyncio.sleep(0.1)

                self.active_tasks -= 1
                self.completed_tasks += 1

                return {"status": "success", "file": str(file_path)}

            async def process_files_concurrently(self, file_paths):
                # Create semaphore to limit concurrency
                semaphore = asyncio.Semaphore(self.max_concurrent)

                async def process_with_semaphore(file_path):
                    async with semaphore:
                        return await self.process_file(file_path)

                # Process all files concurrently
                tasks = [process_with_semaphore(fp) for fp in file_paths]
                results = await asyncio.gather(*tasks)

                return results

        # Test concurrent processing
        processor = ConcurrentProcessor(
            max_concurrent=integration_config["backup"]["resources"]["concurrent_uploads"]
        )

        file_paths = list(source_dir.glob("concurrent_test_*.txt"))
        assert len(file_paths) == 10

        start_time = time.time()
        results = await processor.process_files_concurrently(file_paths)
        duration = time.time() - start_time

        # Verify results
        assert len(results) == 10
        assert all(r["status"] == "success" for r in results)
        assert processor.completed_tasks == 10
        assert processor.max_active <= integration_config["backup"]["resources"]["concurrent_uploads"]

        # Should be faster than sequential processing
        assert duration < 1.0  # Should complete in less than 1 second with concurrency

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
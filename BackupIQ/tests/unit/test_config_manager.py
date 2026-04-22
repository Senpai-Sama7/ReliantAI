#!/usr/bin/env python3
"""
Unit tests for Enterprise Configuration Manager
"""

import pytest
import tempfile
import yaml
import json
from pathlib import Path
from unittest.mock import patch, mock_open
import os

# Import the module to test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from core.config_manager import (
    EnterpriseConfigManager,
    BackupConfig,
    MonitoringConfig,
    SecurityConfig,
    PerformanceConfig
)

class TestEnterpriseConfigManager:
    """Test cases for EnterpriseConfigManager"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary configuration directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_dir = Path(temp_dir) / "config"
            config_dir.mkdir(parents=True)

            # Create subdirectories
            (config_dir / "environments").mkdir()
            (config_dir / "schemas").mkdir()

            yield config_dir

    @pytest.fixture
    def sample_config(self):
        """Sample configuration data"""
        return {
            "version": "1.0.0",
            "backup": {
                "source": {
                    "path": "/test/source",
                    "filters": {
                        "exclude_patterns": ["*.tmp", "*.log"],
                        "max_file_size_mb": 512
                    }
                },
                "destinations": [
                    {
                        "type": "icloud",
                        "config": {"path": "/test/destination"}
                    }
                ],
                "resources": {
                    "max_memory_gb": 2.0,
                    "max_cpu_percent": 50,
                    "concurrent_uploads": 3,
                    "batch_size": 100,
                    "chunk_size_mb": 32
                }
            },
            "monitoring": {
                "enabled": True,
                "endpoints": {
                    "health_port": 8080,
                    "metrics_port": 9090
                },
                "logging": {
                    "level": "INFO",
                    "format": "json",
                    "retention_days": 7
                }
            },
            "security": {
                "encryption": {
                    "enabled": True,
                    "algorithm": "AES-256-GCM"
                },
                "authentication": {
                    "type": "oauth2",
                    "token_expiry_hours": 12
                },
                "audit": {
                    "enabled": True
                }
            },
            "performance": {
                "circuit_breaker": {
                    "failure_threshold": 3,
                    "timeout_seconds": 15
                },
                "retry_policy": {
                    "max_attempts": 2,
                    "backoff_multiplier": 1.5,
                    "initial_delay_ms": 500
                }
            }
        }

    @pytest.fixture
    def sample_schema(self):
        """Sample JSON schema"""
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["version", "backup"],
            "properties": {
                "version": {"type": "string"},
                "backup": {"type": "object"}
            }
        }

    def test_config_manager_initialization(self, temp_config_dir):
        """Test configuration manager initialization"""
        manager = EnterpriseConfigManager(
            config_dir=str(temp_config_dir),
            environment="test"
        )

        assert manager.config_dir == temp_config_dir
        assert manager.environment == "test"
        assert manager._config is None

    def test_load_config_success(self, temp_config_dir, sample_config):
        """Test successful configuration loading"""
        # Write test config file
        config_file = temp_config_dir / "environments" / "test.yml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)

        manager = EnterpriseConfigManager(
            config_dir=str(temp_config_dir),
            environment="test"
        )

        config = manager.load_config()

        assert config == sample_config
        assert config["version"] == "1.0.0"
        assert config["backup"]["source"]["path"] == "/test/source"

    def test_load_config_file_not_found(self, temp_config_dir):
        """Test configuration loading with missing file"""
        manager = EnterpriseConfigManager(
            config_dir=str(temp_config_dir),
            environment="nonexistent"
        )

        with pytest.raises(FileNotFoundError):
            manager.load_config()

    def test_config_validation_success(self, temp_config_dir, sample_config, sample_schema):
        """Test successful configuration validation"""
        # Write config and schema files
        config_file = temp_config_dir / "environments" / "test.yml"
        schema_file = temp_config_dir / "schemas" / "backup_config_schema.json"

        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)

        with open(schema_file, 'w') as f:
            json.dump(sample_schema, f)

        manager = EnterpriseConfigManager(
            config_dir=str(temp_config_dir),
            environment="test"
        )

        # Should not raise an exception
        config = manager.load_config()
        assert config == sample_config

    def test_environment_variable_processing(self, temp_config_dir):
        """Test environment variable substitution"""
        config_with_env = {
            "backup": {
                "source": {
                    "path": "${BACKUP_SOURCE_PATH:/default/path}"
                }
            }
        }

        config_file = temp_config_dir / "environments" / "test.yml"
        with open(config_file, 'w') as f:
            yaml.dump(config_with_env, f)

        manager = EnterpriseConfigManager(
            config_dir=str(temp_config_dir),
            environment="test"
        )

        # Test with environment variable set
        with patch.dict(os.environ, {"BACKUP_SOURCE_PATH": "/env/path"}):
            config = manager.load_config()
            assert config["backup"]["source"]["path"] == "/env/path"

        # Reset for next test
        manager._config = None

        # Test with environment variable not set (should use default)
        with patch.dict(os.environ, {}, clear=True):
            config = manager.load_config()
            assert config["backup"]["source"]["path"] == "/default/path"

    def test_secret_processing(self, temp_config_dir):
        """Test secret reference processing"""
        config_with_secrets = {
            "database": {
                "password": "secret://database/password"
            }
        }

        config_file = temp_config_dir / "environments" / "test.yml"
        with open(config_file, 'w') as f:
            yaml.dump(config_with_secrets, f)

        manager = EnterpriseConfigManager(
            config_dir=str(temp_config_dir),
            environment="test"
        )

        # Mock secret loading
        with patch.dict(os.environ, {"SECRET_DATABASE_PASSWORD": "super-secret"}):
            config = manager.load_config()
            assert config["database"]["password"] == "super-secret"

    def test_get_backup_config(self, temp_config_dir, sample_config):
        """Test getting typed backup configuration"""
        config_file = temp_config_dir / "environments" / "test.yml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)

        manager = EnterpriseConfigManager(
            config_dir=str(temp_config_dir),
            environment="test"
        )

        backup_config = manager.get_backup_config()

        assert isinstance(backup_config, BackupConfig)
        assert backup_config.source_path == "/test/source"
        assert backup_config.max_memory_gb == 2.0
        assert backup_config.concurrent_uploads == 3
        assert backup_config.exclude_patterns == ["*.tmp", "*.log"]

    def test_get_monitoring_config(self, temp_config_dir, sample_config):
        """Test getting typed monitoring configuration"""
        config_file = temp_config_dir / "environments" / "test.yml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)

        manager = EnterpriseConfigManager(
            config_dir=str(temp_config_dir),
            environment="test"
        )

        monitoring_config = manager.get_monitoring_config()

        assert isinstance(monitoring_config, MonitoringConfig)
        assert monitoring_config.enabled is True
        assert monitoring_config.health_port == 8080
        assert monitoring_config.metrics_port == 9090
        assert monitoring_config.log_level == "INFO"
        assert monitoring_config.log_format == "json"

    def test_get_security_config(self, temp_config_dir, sample_config):
        """Test getting typed security configuration"""
        config_file = temp_config_dir / "environments" / "test.yml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)

        manager = EnterpriseConfigManager(
            config_dir=str(temp_config_dir),
            environment="test"
        )

        security_config = manager.get_security_config()

        assert isinstance(security_config, SecurityConfig)
        assert security_config.encryption_enabled is True
        assert security_config.encryption_algorithm == "AES-256-GCM"
        assert security_config.authentication_type == "oauth2"
        assert security_config.token_expiry_hours == 12
        assert security_config.audit_enabled is True

    def test_get_performance_config(self, temp_config_dir, sample_config):
        """Test getting typed performance configuration"""
        config_file = temp_config_dir / "environments" / "test.yml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)

        manager = EnterpriseConfigManager(
            config_dir=str(temp_config_dir),
            environment="test"
        )

        performance_config = manager.get_performance_config()

        assert isinstance(performance_config, PerformanceConfig)
        assert performance_config.circuit_breaker_threshold == 3
        assert performance_config.circuit_breaker_timeout == 15
        assert performance_config.retry_max_attempts == 2
        assert performance_config.retry_backoff_multiplier == 1.5
        assert performance_config.retry_initial_delay_ms == 500

    def test_config_reload(self, temp_config_dir, sample_config):
        """Test configuration reloading"""
        config_file = temp_config_dir / "environments" / "test.yml"
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)

        manager = EnterpriseConfigManager(
            config_dir=str(temp_config_dir),
            environment="test"
        )

        # Load initial config
        config1 = manager.load_config()
        assert config1["backup"]["source"]["path"] == "/test/source"

        # Modify config file
        sample_config["backup"]["source"]["path"] = "/new/source"
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)

        # Reload config
        config2 = manager.reload_config()
        assert config2["backup"]["source"]["path"] == "/new/source"

    def test_validate_config_method(self, temp_config_dir, sample_schema):
        """Test standalone config validation method"""
        schema_file = temp_config_dir / "schemas" / "backup_config_schema.json"
        with open(schema_file, 'w') as f:
            json.dump(sample_schema, f)

        manager = EnterpriseConfigManager(
            config_dir=str(temp_config_dir),
            environment="test"
        )

        # Valid config
        valid_config = {"version": "1.0.0", "backup": {}}
        assert manager.validate_config(valid_config) is True

        # Invalid config
        invalid_config = {"backup": {}}  # Missing required 'version'
        assert manager.validate_config(invalid_config) is False

    def test_default_values(self, temp_config_dir):
        """Test default values when config sections are missing"""
        minimal_config = {
            "version": "1.0.0",
            "backup": {
                "source": {"path": "/test"},
                "destinations": [],
                "resources": {}
            }
        }

        config_file = temp_config_dir / "environments" / "test.yml"
        with open(config_file, 'w') as f:
            yaml.dump(minimal_config, f)

        manager = EnterpriseConfigManager(
            config_dir=str(temp_config_dir),
            environment="test"
        )

        # Test backup config with defaults
        backup_config = manager.get_backup_config()
        assert backup_config.max_memory_gb == 4.0  # Default value
        assert backup_config.max_cpu_percent == 75  # Default value
        assert backup_config.concurrent_uploads == 5  # Default value

        # Test monitoring config with defaults
        monitoring_config = manager.get_monitoring_config()
        assert monitoring_config.enabled is True  # Default value
        assert monitoring_config.health_port == 8080  # Default value
        assert monitoring_config.log_level == "INFO"  # Default value

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
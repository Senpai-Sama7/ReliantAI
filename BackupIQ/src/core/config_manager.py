#!/usr/bin/env python3
"""
Enterprise Configuration Manager
FAANG-grade configuration management with validation, secrets, and environment support
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
from jsonschema import validate, ValidationError
import logging

logger = logging.getLogger(__name__)

@dataclass
class BackupConfig:
    """Enterprise backup configuration"""
    source_path: str
    destinations: list
    max_memory_gb: float = 4.0
    max_cpu_percent: int = 75
    concurrent_uploads: int = 5
    batch_size: int = 500
    chunk_size_mb: int = 64
    exclude_patterns: list = None
    max_file_size_mb: int = 1024

    def __post_init__(self):
        if self.exclude_patterns is None:
            self.exclude_patterns = ["*.tmp", "*.log", "__pycache__", "node_modules", ".git"]

@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    enabled: bool = True
    health_port: int = 8080
    metrics_port: int = 9090
    log_level: str = "INFO"
    log_format: str = "json"
    retention_days: int = 30

@dataclass
class SecurityConfig:
    """Security configuration"""
    encryption_enabled: bool = True
    encryption_algorithm: str = "AES-256-GCM"
    authentication_type: str = "oauth2"
    token_expiry_hours: int = 24
    audit_enabled: bool = True

@dataclass
class PerformanceConfig:
    """Performance configuration"""
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: int = 30
    retry_max_attempts: int = 3
    retry_backoff_multiplier: float = 2.0
    retry_initial_delay_ms: int = 1000

class EnterpriseConfigManager:
    """Enterprise configuration manager with validation and secrets support"""

    def __init__(self, config_dir: str = "config", environment: str = "development"):
        self.config_dir = Path(config_dir)
        self.environment = environment
        self.schema_dir = self.config_dir / "schemas"
        self.env_dir = self.config_dir / "environments"

        self._config: Optional[Dict[str, Any]] = None
        self._schema: Optional[Dict[str, Any]] = None

    def load_config(self) -> Dict[str, Any]:
        """Load and validate configuration"""
        if self._config is not None:
            return self._config

        # Load environment-specific config
        config_file = self.env_dir / f"{self.environment}.yml"
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_file}")

        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f)

        # Load and validate against schema
        schema = self._load_schema()
        if schema:
            try:
                validate(instance=config_data, schema=schema)
                logger.info(f"Configuration validated successfully for environment: {self.environment}")
            except ValidationError as e:
                logger.error(f"Configuration validation failed: {e.message}")
                raise

        # Process environment variables and secrets
        config_data = self._process_environment_variables(config_data)
        config_data = self._process_secrets(config_data)

        self._config = config_data
        return self._config

    def _load_schema(self) -> Optional[Dict[str, Any]]:
        """Load configuration schema"""
        if self._schema is not None:
            return self._schema

        schema_file = self.schema_dir / "backup_config_schema.json"
        if not schema_file.exists():
            logger.warning("Configuration schema not found")
            return None

        with open(schema_file, 'r') as f:
            self._schema = json.load(f)

        return self._schema

    def _process_environment_variables(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Process environment variable references in config"""
        def replace_env_vars(obj):
            if isinstance(obj, dict):
                return {k: replace_env_vars(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_env_vars(item) for item in obj]
            elif isinstance(obj, str) and obj.startswith("${") and obj.endswith("}"):
                env_var = obj[2:-1]
                default_value = None
                if ":" in env_var:
                    env_var, default_value = env_var.split(":", 1)
                return os.getenv(env_var, default_value)
            return obj

        return replace_env_vars(config)

    def _process_secrets(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Process secret references in config"""
        def replace_secrets(obj):
            if isinstance(obj, dict):
                return {k: replace_secrets(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_secrets(item) for item in obj]
            elif isinstance(obj, str) and obj.startswith("secret://"):
                secret_path = obj[9:]  # Remove 'secret://' prefix
                return self._load_secret(secret_path)
            return obj

        return replace_secrets(config)

    def _load_secret(self, secret_path: str) -> str:
        """Load secret from secure storage"""
        # In production, integrate with AWS Secrets Manager, HashiCorp Vault, etc.
        # For now, load from environment variables with SECRET_ prefix
        env_var = f"SECRET_{secret_path.upper().replace('/', '_')}"
        secret_value = os.getenv(env_var)

        if secret_value is None:
            logger.warning(f"Secret not found: {secret_path}")
            return f"<SECRET:{secret_path}>"

        return secret_value

    def get_backup_config(self) -> BackupConfig:
        """Get typed backup configuration"""
        config = self.load_config()
        backup_section = config.get("backup", {})

        return BackupConfig(
            source_path=backup_section.get("source", {}).get("path", "/data/backup-source"),
            destinations=backup_section.get("destinations", []),
            max_memory_gb=backup_section.get("resources", {}).get("max_memory_gb", 4.0),
            max_cpu_percent=backup_section.get("resources", {}).get("max_cpu_percent", 75),
            concurrent_uploads=backup_section.get("resources", {}).get("concurrent_uploads", 5),
            batch_size=backup_section.get("resources", {}).get("batch_size", 500),
            chunk_size_mb=backup_section.get("resources", {}).get("chunk_size_mb", 64),
            exclude_patterns=backup_section.get("source", {}).get("filters", {}).get("exclude_patterns", None),
            max_file_size_mb=backup_section.get("source", {}).get("filters", {}).get("max_file_size_mb", 1024)
        )

    def get_monitoring_config(self) -> MonitoringConfig:
        """Get typed monitoring configuration"""
        config = self.load_config()
        monitoring_section = config.get("monitoring", {})

        return MonitoringConfig(
            enabled=monitoring_section.get("enabled", True),
            health_port=monitoring_section.get("endpoints", {}).get("health_port", 8080),
            metrics_port=monitoring_section.get("endpoints", {}).get("metrics_port", 9090),
            log_level=monitoring_section.get("logging", {}).get("level", "INFO"),
            log_format=monitoring_section.get("logging", {}).get("format", "json"),
            retention_days=monitoring_section.get("logging", {}).get("retention_days", 30)
        )

    def get_security_config(self) -> SecurityConfig:
        """Get typed security configuration"""
        config = self.load_config()
        security_section = config.get("security", {})

        return SecurityConfig(
            encryption_enabled=security_section.get("encryption", {}).get("enabled", True),
            encryption_algorithm=security_section.get("encryption", {}).get("algorithm", "AES-256-GCM"),
            authentication_type=security_section.get("authentication", {}).get("type", "oauth2"),
            token_expiry_hours=security_section.get("authentication", {}).get("token_expiry_hours", 24),
            audit_enabled=security_section.get("audit", {}).get("enabled", True)
        )

    def get_performance_config(self) -> PerformanceConfig:
        """Get typed performance configuration"""
        config = self.load_config()
        performance_section = config.get("performance", {})

        return PerformanceConfig(
            circuit_breaker_threshold=performance_section.get("circuit_breaker", {}).get("failure_threshold", 5),
            circuit_breaker_timeout=performance_section.get("circuit_breaker", {}).get("timeout_seconds", 30),
            retry_max_attempts=performance_section.get("retry_policy", {}).get("max_attempts", 3),
            retry_backoff_multiplier=performance_section.get("retry_policy", {}).get("backoff_multiplier", 2.0),
            retry_initial_delay_ms=performance_section.get("retry_policy", {}).get("initial_delay_ms", 1000)
        )

    def get_raw_config(self) -> Dict[str, Any]:
        """Get raw configuration dictionary"""
        return self.load_config()

    def reload_config(self):
        """Reload configuration from files"""
        self._config = None
        self._schema = None
        return self.load_config()

    def validate_config(self, config_data: Dict[str, Any]) -> bool:
        """Validate configuration against schema"""
        schema = self._load_schema()
        if not schema:
            return True

        try:
            validate(instance=config_data, schema=schema)
            return True
        except ValidationError as e:
            logger.error(f"Configuration validation failed: {e.message}")
            return False
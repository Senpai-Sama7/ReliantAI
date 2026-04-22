#!/usr/bin/env python3
"""
Enterprise Monitoring System
FAANG-grade observability with metrics, logging, and health checks
"""

import time
import json
import logging
import threading
import contextvars
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from contextlib import contextmanager
import structlog
import uuid

# Prometheus Metrics
backup_files_processed = Counter('backup_files_processed_total', 'Total files processed', ['status', 'file_type'])
backup_duration = Histogram('backup_operation_duration_seconds', 'Backup operation duration')
backup_errors = Counter('backup_errors_total', 'Total backup errors', ['error_type', 'severity'])
system_resource_usage = Gauge('system_resource_usage_percent', 'System resource usage', ['resource_type'])
active_operations = Gauge('backup_active_operations', 'Currently active backup operations')

@dataclass
class CorrelationContext:
    """Correlation context for distributed tracing"""
    correlation_id: str
    operation_id: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    start_time: float = 0.0

class EnterpriseLogger:
    """Enterprise-grade structured logger"""

    def __init__(self, service_name: str = "backup-service", log_level: str = "INFO"):
        self.service_name = service_name

        # Configure structlog for JSON logging
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="ISO"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        # Setup standard logger
        logging.basicConfig(
            format="%(message)s",
            level=getattr(logging, log_level.upper()),
        )

        self.logger = structlog.get_logger()

    def get_logger(self, **context) -> structlog.BoundLogger:
        """Get logger with context"""
        return self.logger.bind(
            service=self.service_name,
            **context
        )

class EnterpriseMetrics:
    """Enterprise metrics collection and reporting"""

    def __init__(self, port: int = 9090):
        self.port = port
        self.custom_metrics: Dict[str, Any] = {}
        self.start_time = time.time()

    def start_metrics_server(self):
        """Start Prometheus metrics server"""
        start_http_server(self.port)

    def record_file_processed(self, status: str = "success", file_type: str = "unknown"):
        """Record file processing metric"""
        backup_files_processed.labels(status=status, file_type=file_type).inc()

    def record_operation_duration(self, duration_seconds: float):
        """Record operation duration"""
        backup_duration.observe(duration_seconds)

    def record_error(self, error_type: str, severity: str = "medium"):
        """Record error occurrence"""
        backup_errors.labels(error_type=error_type, severity=severity).inc()

    def update_resource_usage(self, resource_type: str, usage_percent: float):
        """Update resource usage metric"""
        system_resource_usage.labels(resource_type=resource_type).set(usage_percent)

    def set_active_operations(self, count: int):
        """Set number of active operations"""
        active_operations.set(count)

class EnterpriseHealthChecker:
    """Enterprise health checking system"""

    def __init__(self):
        self.checks: Dict[str, bool] = {}
        self.last_check_times: Dict[str, float] = {}

    def register_check(self, name: str, check_func: callable, interval: int = 30):
        """Register a health check"""
        def run_check():
            while True:
                try:
                    result = check_func()
                    self.checks[name] = result
                    self.last_check_times[name] = time.time()
                except Exception as e:
                    logging.getLogger(__name__).warning(
                        f"Health check '{name}' failed: {type(e).__name__}: {str(e)}",
                        extra={"health_check": name, "exception": type(e).__name__, "error": str(e)}
                    )
                    self.checks[name] = False
                    self.last_check_times[name] = time.time()
                time.sleep(interval)

        thread = threading.Thread(target=run_check, daemon=True)
        thread.start()

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall health status"""
        now = time.time()
        overall_healthy = all(self.checks.values())

        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "uptime_seconds": int(now - getattr(self, 'start_time', now)),
            "checks": {
                name: {
                    "status": "passing" if status else "failing",
                    "last_check": datetime.fromtimestamp(
                        self.last_check_times.get(name, 0), timezone.utc
                    ).isoformat() if name in self.last_check_times else None
                }
                for name, status in self.checks.items()
            }
        }

class EnterpriseAuditLogger:
    """Enterprise audit logging for compliance"""

    def __init__(self, logger: EnterpriseLogger):
        self.logger = logger.get_logger().bind(audit=True)

    def log_access(self, user_id: str, resource: str, action: str, result: str):
        """Log access attempt"""
        self.logger.info(
            "Access attempt",
            user_id=user_id,
            resource=resource,
            action=action,
            result=result,
            event_type="access"
        )

    def log_data_operation(self, operation: str, data_type: str, count: int, user_id: str):
        """Log data operation"""
        self.logger.info(
            "Data operation",
            operation=operation,
            data_type=data_type,
            record_count=count,
            user_id=user_id,
            event_type="data_operation"
        )

    def log_system_event(self, event: str, severity: str, details: Dict[str, Any]):
        """Log system event"""
        self.logger.info(
            "System event",
            event=event,
            severity=severity,
            event_type="system",
            **details
        )

class EnterpriseMonitoring:
    """Main enterprise monitoring orchestrator"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = EnterpriseLogger(
            service_name=config.get('service_name', 'backup-service'),
            log_level=config.get('log_level', 'INFO')
        )
        self.metrics = EnterpriseMetrics(port=config.get('metrics_port', 9090))
        self.health_checker = EnterpriseHealthChecker()
        self.audit_logger = EnterpriseAuditLogger(self.logger)

        # Correlation context (async-safe using contextvars)
        self._correlation_context_var: contextvars.ContextVar[Optional[CorrelationContext]] = \
            contextvars.ContextVar('correlation_context', default=None)

    def initialize(self):
        """Initialize monitoring systems"""
        self.metrics.start_metrics_server()

        # Register default health checks
        self.health_checker.register_check("system_resources", self._check_system_resources)
        self.health_checker.register_check("disk_space", self._check_disk_space)

        self.logger.get_logger().info("Enterprise monitoring initialized")

    def _check_system_resources(self) -> bool:
        """Check system resource availability"""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent

            self.metrics.update_resource_usage("cpu", cpu_percent)
            self.metrics.update_resource_usage("memory", memory_percent)

            return cpu_percent < 90 and memory_percent < 90
        except ImportError:
            return True  # Skip check if psutil not available

    def _check_disk_space(self) -> bool:
        """Check disk space availability"""
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            disk_percent = (used / total) * 100

            self.metrics.update_resource_usage("disk", disk_percent)
            return disk_percent < 90
        except (OSError, RuntimeError) as e:
            self.logger.get_logger().warning(
                f"Disk space check failed: {type(e).__name__}: {str(e)}",
                extra={"exception": type(e).__name__, "error": str(e)}
            )
            return True  # Assume healthy if check fails
        except ImportError:
            return True  # Skip check if shutil not available

    @contextmanager
    def operation_context(self, operation_name: str, **metadata):
        """Context manager for operation tracking"""
        correlation_id = str(uuid.uuid4())
        operation_id = f"{operation_name}_{int(time.time())}"

        # Set correlation context (async-safe)
        context = CorrelationContext(
            correlation_id=correlation_id,
            operation_id=operation_id,
            start_time=time.time()
        )
        token = self._correlation_context_var.set(context)

        # Get logger with correlation context
        logger = self.logger.get_logger(
            correlation_id=correlation_id,
            operation_id=operation_id,
            **metadata
        )

        logger.info(f"Starting {operation_name}")

        try:
            yield logger
            duration = time.time() - context.start_time
            self.metrics.record_operation_duration(duration)
            logger.info(f"Completed {operation_name}", duration_seconds=duration)

        except Exception as e:
            duration = time.time() - context.start_time
            self.metrics.record_error(str(type(e).__name__), "high")
            logger.error(f"Failed {operation_name}",
                        duration_seconds=duration,
                        error=str(e))
            raise
        finally:
            # Reset context after operation completes
            self._correlation_context_var.reset(token)

    def get_current_context(self) -> Optional[CorrelationContext]:
        """Get current correlation context (async-safe)"""
        return self._correlation_context_var.get()

    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        return self.health_checker.get_health_status()

# Factory function for easy initialization
def create_monitoring(config: Dict[str, Any]) -> EnterpriseMonitoring:
    """Factory function to create enterprise monitoring"""
    monitoring = EnterpriseMonitoring(config)
    monitoring.initialize()
    return monitoring
#!/usr/bin/env python3
"""
Enterprise Backup Orchestrator
FAANG-grade backup workflow coordination with semantic file organization
"""

import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib

from .config_manager import EnterpriseConfigManager, BackupConfig
from .exceptions import (
    BackupOperationError, FileDiscoveryError, InvalidPathError,
    ResourceExhaustedError, BackupInProgressError
)
from .circuit_breaker import CircuitBreaker
from .retry_logic import RetryConfig, with_retry, STANDARD_RETRY_CONFIG
from ..storage.base import CloudStorageProvider
from ..storage.s3_provider import S3StorageProvider
from ..storage.gcs_provider import GCSStorageProvider
from ..storage.icloud_provider import iCloudStorageProvider
from ..storage.azure_provider import AzureBlobStorageProvider
from ..monitoring.enterprise_monitoring import EnterpriseMonitoring

logger = logging.getLogger(__name__)


@dataclass
class FileMetadata:
    """Metadata for discovered files"""
    path: str
    size_bytes: int
    modified_time: datetime
    checksum: Optional[str] = None
    file_type: str = "unknown"
    importance_score: float = 0.5
    semantic_tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "path": self.path,
            "size_bytes": self.size_bytes,
            "size_mb": round(self.size_bytes / (1024**2), 2),
            "modified_time": self.modified_time.isoformat(),
            "checksum": self.checksum,
            "file_type": self.file_type,
            "importance_score": self.importance_score,
            "semantic_tags": self.semantic_tags
        }


@dataclass
class BackupProgress:
    """Backup operation progress tracking"""
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    skipped_files: int = 0
    total_bytes: int = 0
    uploaded_bytes: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str = "pending"  # pending, running, completed, failed
    errors: List[str] = field(default_factory=list)

    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage"""
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100

    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.processed_files == 0:
            return 0.0
        return ((self.processed_files - self.failed_files) / self.processed_files) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "failed_files": self.failed_files,
            "skipped_files": self.skipped_files,
            "total_bytes": self.total_bytes,
            "uploaded_bytes": self.uploaded_bytes,
            "total_gb": round(self.total_bytes / (1024**3), 2),
            "uploaded_gb": round(self.uploaded_bytes / (1024**3), 2),
            "progress_percent": round(self.progress_percent, 2),
            "success_rate": round(self.success_rate, 2),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "status": self.status,
            "errors": self.errors[:10]  # Limit to 10 most recent errors
        }


class EnterpriseBackupOrchestrator:
    """
    Enterprise backup orchestrator - coordinates entire backup workflow

    Features:
    - File discovery with filtering
    - Batch processing with resource management
    - Multi-cloud upload support
    - Progress tracking and reporting
    - Error handling and recovery
    - Circuit breaker integration
    - Retry logic for failures
    """

    def __init__(
        self,
        config_manager: EnterpriseConfigManager,
        monitoring: Optional[EnterpriseMonitoring] = None
    ):
        """
        Initialize backup orchestrator

        Args:
            config_manager: Configuration manager instance
            monitoring: Optional monitoring system
        """
        self.config_manager = config_manager
        self.backup_config = config_manager.get_backup_config()
        self.performance_config = config_manager.get_performance_config()
        self.monitoring = monitoring

        # State management
        self._is_running = False
        self._progress = BackupProgress()

        # Storage providers
        self._storage_providers: Dict[str, CloudStorageProvider] = {}

        # Circuit breakers for each storage provider
        self._circuit_breakers: Dict[str, CircuitBreaker] = {}

        # Concurrency control
        self._semaphore = asyncio.Semaphore(self.backup_config.concurrent_uploads)

        logger.info("Enterprise Backup Orchestrator initialized")

    async def initialize(self):
        """Initialize backup orchestrator"""
        # Initialize storage providers
        await self._initialize_storage_providers()

        logger.info("Backup orchestrator initialization complete")

    async def _initialize_storage_providers(self):
        """Initialize cloud storage providers"""
        for dest_config in self.backup_config.destinations:
            provider_type = dest_config.get("type")
            provider_config = dest_config.get("config", {})

            try:
                if provider_type == "s3":
                    provider = S3StorageProvider(provider_config)
                elif provider_type == "gcs" or provider_type == "gdrive":
                    provider = GCSStorageProvider(provider_config)
                elif provider_type == "icloud":
                    provider = iCloudStorageProvider(provider_config)
                elif provider_type == "azure":
                    provider = AzureBlobStorageProvider(provider_config)
                else:
                    logger.warning(f"Unknown storage provider type: {provider_type}")
                    continue

                # Authenticate
                await provider.authenticate()

                self._storage_providers[provider_type] = provider

                # Create circuit breaker for this provider
                self._circuit_breakers[provider_type] = CircuitBreaker(
                    failure_threshold=self.performance_config.circuit_breaker_threshold,
                    timeout=self.performance_config.circuit_breaker_timeout,
                    name=f"{provider_type}_storage"
                )

                logger.info(f"Initialized storage provider: {provider_type}")

            except Exception as e:
                logger.error(
                    f"Failed to initialize {provider_type} provider: {str(e)}",
                    extra={"provider": provider_type, "error": str(e)}
                )

        if not self._storage_providers:
            raise BackupOperationError(
                "No storage providers initialized",
                details={"configured_providers": [d.get("type") for d in self.backup_config.destinations]}
            )

    async def discover_files(self) -> List[FileMetadata]:
        """
        Discover files to backup

        Returns:
            List of file metadata objects

        Raises:
            FileDiscoveryError: If discovery fails
        """
        source_path = Path(self.backup_config.source_path)

        if not source_path.exists():
            raise InvalidPathError(f"Source path does not exist: {source_path}")

        if not source_path.is_dir():
            raise InvalidPathError(f"Source path is not a directory: {source_path}")

        discovered_files: List[FileMetadata] = []
        exclude_patterns = set(self.backup_config.exclude_patterns)

        try:
            logger.info(f"Discovering files in: {source_path}")

            for root, dirs, files in os.walk(source_path):
                # Filter directories
                dirs[:] = [d for d in dirs if not self._should_exclude(d, exclude_patterns)]

                for filename in files:
                    if self._should_exclude(filename, exclude_patterns):
                        continue

                    file_path = Path(root) / filename

                    try:
                        stat = file_path.stat()

                        # Check file size limit
                        size_mb = stat.st_size / (1024 ** 2)
                        if size_mb > self.backup_config.max_file_size_mb:
                            logger.debug(f"Skipping large file: {file_path} ({size_mb:.2f}MB)")
                            continue

                        # Create file metadata
                        metadata = FileMetadata(
                            path=str(file_path),
                            size_bytes=stat.st_size,
                            modified_time=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
                            file_type=self._classify_file_type(file_path)
                        )

                        discovered_files.append(metadata)

                    except (OSError, PermissionError) as e:
                        logger.warning(f"Cannot access file {file_path}: {str(e)}")
                        continue

            logger.info(
                f"Discovered {len(discovered_files)} files totaling "
                f"{sum(f.size_bytes for f in discovered_files) / (1024**3):.2f} GB"
            )

            return discovered_files

        except Exception as e:
            logger.error(f"File discovery failed: {str(e)}")
            raise FileDiscoveryError(
                f"Failed to discover files: {str(e)}",
                details={"source_path": str(source_path), "error": str(e)}
            )

    def _should_exclude(self, name: str, exclude_patterns: Set[str]) -> bool:
        """Check if file/directory should be excluded"""
        from fnmatch import fnmatch
        return any(fnmatch(name, pattern) for pattern in exclude_patterns)

    def _classify_file_type(self, file_path: Path) -> str:
        """Classify file type based on extension"""
        ext = file_path.suffix.lower()

        type_map = {
            # Code
            '.py': 'code', '.js': 'code', '.ts': 'code', '.java': 'code',
            '.cpp': 'code', '.c': 'code', '.go': 'code', '.rs': 'code',
            '.rb': 'code', '.php': 'code', '.swift': 'code', '.kt': 'code',

            # Documents
            '.pdf': 'document', '.doc': 'document', '.docx': 'document',
            '.txt': 'document', '.md': 'document', '.rtf': 'document',

            # Images
            '.jpg': 'image', '.jpeg': 'image', '.png': 'image',
            '.gif': 'image', '.bmp': 'image', '.svg': 'image',

            # Videos
            '.mp4': 'video', '.avi': 'video', '.mov': 'video',
            '.mkv': 'video', '.wmv': 'video',

            # Audio
            '.mp3': 'audio', '.wav': 'audio', '.flac': 'audio',
            '.m4a': 'audio', '.ogg': 'audio',

            # Archives
            '.zip': 'archive', '.tar': 'archive', '.gz': 'archive',
            '.rar': 'archive', '.7z': 'archive',

            # Data
            '.json': 'data', '.xml': 'data', '.csv': 'data',
            '.yaml': 'data', '.yml': 'data', '.toml': 'data',

            # Database
            '.db': 'database', '.sqlite': 'database', '.sql': 'database',
        }

        return type_map.get(ext, 'unknown')

    async def backup_files(
        self,
        files: Optional[List[FileMetadata]] = None,
        destination_filter: Optional[List[str]] = None
    ) -> BackupProgress:
        """
        Execute backup workflow

        Args:
            files: Optional list of files to backup (if None, discover automatically)
            destination_filter: Optional list of destination types to use

        Returns:
            BackupProgress with results

        Raises:
            BackupInProgressError: If backup already running
            BackupOperationError: If backup fails
        """
        if self._is_running:
            raise BackupInProgressError("Backup operation already in progress")

        self._is_running = True
        self._progress = BackupProgress(
            start_time=datetime.now(timezone.utc),
            status="running"
        )

        try:
            # Discover files if not provided
            if files is None:
                files = await self.discover_files()

            self._progress.total_files = len(files)
            self._progress.total_bytes = sum(f.size_bytes for f in files)

            logger.info(
                f"Starting backup of {self._progress.total_files} files "
                f"({self._progress.total_bytes / (1024**3):.2f} GB)"
            )

            # Filter storage providers if requested
            providers = self._storage_providers
            if destination_filter:
                providers = {
                    k: v for k, v in providers.items()
                    if k in destination_filter
                }

            # Process files in batches
            batch_size = self.backup_config.batch_size
            for i in range(0, len(files), batch_size):
                batch = files[i:i + batch_size]

                # Upload batch concurrently
                tasks = []
                for file_meta in batch:
                    for provider_type, provider in providers.items():
                        task = self._upload_file_with_retry(
                            file_meta,
                            provider,
                            provider_type
                        )
                        tasks.append(task)

                # Wait for batch to complete
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Process results
                for result in results:
                    if isinstance(result, Exception):
                        self._progress.failed_files += 1
                        self._progress.errors.append(str(result))
                        logger.error(f"Upload failed: {str(result)}")
                    else:
                        self._progress.processed_files += 1
                        if result:
                            self._progress.uploaded_bytes += result.bytes_uploaded

                # Log progress
                if self.monitoring:
                    self.monitoring.metrics.record_file_processed("success", "batch")

                logger.info(
                    f"Batch progress: {self._progress.processed_files}/{self._progress.total_files} "
                    f"({self._progress.progress_percent:.1f}%)"
                )

            # Mark as completed
            self._progress.end_time = datetime.now(timezone.utc)
            self._progress.status = "completed" if self._progress.failed_files == 0 else "completed_with_errors"

            logger.info(
                f"Backup completed: {self._progress.processed_files} files, "
                f"{self._progress.failed_files} failures, "
                f"{self._progress.success_rate:.1f}% success rate"
            )

            return self._progress

        except Exception as e:
            self._progress.status = "failed"
            self._progress.end_time = datetime.now(timezone.utc)
            self._progress.errors.append(str(e))

            logger.error(f"Backup operation failed: {str(e)}")

            raise BackupOperationError(
                f"Backup failed: {str(e)}",
                details={"progress": self._progress.to_dict(), "error": str(e)}
            )

        finally:
            self._is_running = False

    async def _upload_file_with_retry(
        self,
        file_meta: FileMetadata,
        provider: CloudStorageProvider,
        provider_type: str
    ):
        """Upload file with circuit breaker and retry logic"""
        async with self._semaphore:  # Limit concurrent uploads
            circuit_breaker = self._circuit_breakers[provider_type]

            @with_retry(RetryConfig(
                max_attempts=self.performance_config.retry_max_attempts,
                base_delay=self.performance_config.retry_initial_delay_ms / 1000,
                backoff_factor=self.performance_config.retry_backoff_multiplier
            ))
            async def upload():
                return await circuit_breaker.call_async(
                    provider.upload_file,
                    file_meta.path,
                    self._get_remote_path(file_meta.path)
                )

            try:
                result = await upload()

                if self.monitoring:
                    self.monitoring.metrics.record_file_processed("success", file_meta.file_type)

                return result

            except Exception as e:
                if self.monitoring:
                    self.monitoring.metrics.record_file_processed("failure", file_meta.file_type)
                    self.monitoring.metrics.record_error(type(e).__name__, "high")

                raise

    def _get_remote_path(self, local_path: str) -> str:
        """Generate remote path from local path"""
        source_path = Path(self.backup_config.source_path)
        file_path = Path(local_path)

        try:
            relative_path = file_path.relative_to(source_path)
            return str(relative_path)
        except ValueError:
            # If not relative, use just the filename
            return file_path.name

    def get_progress(self) -> BackupProgress:
        """Get current backup progress"""
        return self._progress

    def is_running(self) -> bool:
        """Check if backup is currently running"""
        return self._is_running

    async def cancel_backup(self):
        """Cancel running backup operation"""
        if self._is_running:
            logger.warning("Cancelling backup operation")
            self._is_running = False
            self._progress.status = "cancelled"
            self._progress.end_time = datetime.now(timezone.utc)


# CLI entry point
def main():
    """Main entry point for CLI"""
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # Load configuration
        environment = os.getenv("ENVIRONMENT", "development")
        config_manager = EnterpriseConfigManager(environment=environment)

        # Create orchestrator
        orchestrator = EnterpriseBackupOrchestrator(config_manager)

        # Run backup
        asyncio.run(orchestrator.initialize())
        progress = asyncio.run(orchestrator.backup_files())

        print(f"\nBackup completed:")
        print(f"  Total files: {progress.total_files}")
        print(f"  Processed: {progress.processed_files}")
        print(f"  Failed: {progress.failed_files}")
        print(f"  Success rate: {progress.success_rate:.1f}%")
        print(f"  Total uploaded: {progress.uploaded_bytes / (1024**3):.2f} GB")

        sys.exit(0 if progress.failed_files == 0 else 1)

    except Exception as e:
        print(f"ERROR: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

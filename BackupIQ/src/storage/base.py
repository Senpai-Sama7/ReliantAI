#!/usr/bin/env python3
"""
Base Cloud Storage Provider Interface
Abstract base class for all cloud storage implementations
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from pathlib import Path


@dataclass
class StorageInfo:
    """Cloud storage information"""
    total_bytes: int
    used_bytes: int
    free_bytes: int
    provider: str
    quota_exceeded: bool = False

    @property
    def usage_percent(self) -> float:
        """Calculate usage percentage"""
        if self.total_bytes == 0:
            return 0.0
        return (self.used_bytes / self.total_bytes) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "total_bytes": self.total_bytes,
            "used_bytes": self.used_bytes,
            "free_bytes": self.free_bytes,
            "total_gb": round(self.total_bytes / (1024**3), 2),
            "used_gb": round(self.used_bytes / (1024**3), 2),
            "free_gb": round(self.free_bytes / (1024**3), 2),
            "usage_percent": round(self.usage_percent, 2),
            "provider": self.provider,
            "quota_exceeded": self.quota_exceeded
        }


@dataclass
class UploadResult:
    """Upload operation result"""
    success: bool
    remote_path: str
    bytes_uploaded: int
    duration_seconds: float
    checksum: Optional[str] = None
    version_id: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "remote_path": self.remote_path,
            "bytes_uploaded": self.bytes_uploaded,
            "mb_uploaded": round(self.bytes_uploaded / (1024**2), 2),
            "duration_seconds": round(self.duration_seconds, 2),
            "throughput_mbps": round((self.bytes_uploaded / (1024**2)) / max(self.duration_seconds, 0.001), 2),
            "checksum": self.checksum,
            "version_id": self.version_id,
            "error": self.error
        }


@dataclass
class FileInfo:
    """Cloud file information"""
    path: str
    size_bytes: int
    modified_time: datetime
    checksum: Optional[str] = None
    content_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "path": self.path,
            "size_bytes": self.size_bytes,
            "size_mb": round(self.size_bytes / (1024**2), 2),
            "modified_time": self.modified_time.isoformat(),
            "checksum": self.checksum,
            "content_type": self.content_type,
            "metadata": self.metadata
        }


@dataclass
class DownloadResult:
    """Download operation result"""
    success: bool
    local_path: str
    bytes_downloaded: int
    duration_seconds: float
    checksum: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "success": self.success,
            "local_path": self.local_path,
            "bytes_downloaded": self.bytes_downloaded,
            "mb_downloaded": round(self.bytes_downloaded / (1024**2), 2),
            "duration_seconds": round(self.duration_seconds, 2),
            "throughput_mbps": round((self.bytes_downloaded / (1024**2)) / max(self.duration_seconds, 0.001), 2),
            "checksum": self.checksum,
            "error": self.error
        }


class CloudStorageProvider(ABC):
    """
    Abstract base class for cloud storage providers

    All cloud storage providers must implement this interface to ensure
    consistent behavior across different cloud providers (S3, iCloud, GCS, Azure).
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize cloud storage provider

        Args:
            config: Provider-specific configuration
        """
        self.config = config
        self.provider_name = "unknown"
        self._authenticated = False

    @abstractmethod
    async def authenticate(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
        """
        Authenticate with cloud storage provider

        Args:
            credentials: Optional credentials dictionary
                        If not provided, use credentials from config

        Returns:
            True if authentication successful, False otherwise

        Raises:
            StorageAuthenticationError: If authentication fails
        """
        pass

    @abstractmethod
    async def upload_file(
        self,
        local_path: str,
        remote_path: str,
        chunk_size: int = 64 * 1024 * 1024,  # 64MB default
        progress_callback: Optional[Callable[[int, int], None]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UploadResult:
        """
        Upload file to cloud storage

        Args:
            local_path: Local file path
            remote_path: Remote destination path
            chunk_size: Upload chunk size in bytes
            progress_callback: Optional callback function(bytes_uploaded, total_bytes)
            metadata: Optional file metadata

        Returns:
            UploadResult with upload details

        Raises:
            StorageUploadError: If upload fails
            InvalidPathError: If local_path doesn't exist
        """
        pass

    @abstractmethod
    async def download_file(
        self,
        remote_path: str,
        local_path: str,
        chunk_size: int = 64 * 1024 * 1024,  # 64MB default
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> DownloadResult:
        """
        Download file from cloud storage

        Args:
            remote_path: Remote file path
            local_path: Local destination path
            chunk_size: Download chunk size in bytes
            progress_callback: Optional callback function(bytes_downloaded, total_bytes)

        Returns:
            DownloadResult with download details

        Raises:
            StorageDownloadError: If download fails
        """
        pass

    @abstractmethod
    async def delete_file(self, remote_path: str) -> bool:
        """
        Delete file from cloud storage

        Args:
            remote_path: Remote file path

        Returns:
            True if deletion successful

        Raises:
            StorageError: If deletion fails
        """
        pass

    @abstractmethod
    async def list_files(
        self,
        path: str = "",
        recursive: bool = False,
        max_results: Optional[int] = None
    ) -> List[FileInfo]:
        """
        List files in cloud storage

        Args:
            path: Directory path to list
            recursive: Whether to list recursively
            max_results: Maximum number of results to return

        Returns:
            List of FileInfo objects

        Raises:
            StorageError: If listing fails
        """
        pass

    @abstractmethod
    async def file_exists(self, remote_path: str) -> bool:
        """
        Check if file exists in cloud storage

        Args:
            remote_path: Remote file path

        Returns:
            True if file exists, False otherwise
        """
        pass

    @abstractmethod
    async def get_file_info(self, remote_path: str) -> Optional[FileInfo]:
        """
        Get file information

        Args:
            remote_path: Remote file path

        Returns:
            FileInfo if file exists, None otherwise
        """
        pass

    @abstractmethod
    async def check_space(self) -> StorageInfo:
        """
        Check available storage space

        Returns:
            StorageInfo with storage details

        Raises:
            StorageError: If check fails
        """
        pass

    @abstractmethod
    async def create_directory(self, path: str) -> bool:
        """
        Create directory in cloud storage

        Args:
            path: Directory path to create

        Returns:
            True if creation successful

        Raises:
            StorageError: If creation fails
        """
        pass

    @abstractmethod
    async def delete_directory(self, path: str, recursive: bool = False) -> bool:
        """
        Delete directory from cloud storage

        Args:
            path: Directory path to delete
            recursive: Whether to delete recursively

        Returns:
            True if deletion successful

        Raises:
            StorageError: If deletion fails
        """
        pass

    async def validate_path(self, path: str) -> bool:
        """
        Validate path format

        Args:
            path: Path to validate

        Returns:
            True if path is valid

        Raises:
            InvalidPathError: If path is invalid
        """
        from ..core.exceptions import InvalidPathError

        if not path:
            raise InvalidPathError("Path cannot be empty")

        # Check for invalid characters (provider-specific validation should override this)
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in path for char in invalid_chars):
            raise InvalidPathError(f"Path contains invalid characters: {path}")

        return True

    def is_authenticated(self) -> bool:
        """Check if provider is authenticated"""
        return self._authenticated

    def get_provider_name(self) -> str:
        """Get provider name"""
        return self.provider_name

    def get_config(self) -> Dict[str, Any]:
        """Get provider configuration"""
        return self.config.copy()

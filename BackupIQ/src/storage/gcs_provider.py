#!/usr/bin/env python3
"""
Google Cloud Storage Provider
Production-grade GCS integration
"""

import time
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timezone

from google.cloud import storage
from google.api_core import exceptions as gcp_exceptions
from google.oauth2 import service_account

from .base import CloudStorageProvider, StorageInfo, UploadResult, FileInfo, DownloadResult
from ..core.exceptions import (
    StorageAuthenticationError, StorageUploadError, StorageDownloadError,
    StorageError, InvalidPathError, StorageConnectionError
)

logger = logging.getLogger(__name__)


class GCSStorageProvider(CloudStorageProvider):
    """Google Cloud Storage provider with production-grade features"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize GCS provider

        Required config:
            - bucket: GCS bucket name
            - project_id: GCP project ID

        Optional config:
            - credentials_json: Path to service account JSON file
            - credentials_dict: Service account credentials as dictionary
            - storage_class: Storage class (STANDARD, NEARLINE, COLDLINE, ARCHIVE)
        """
        super().__init__(config)
        self.provider_name = "Google Cloud Storage"

        self.bucket_name = config.get("bucket")
        self.project_id = config.get("project_id")
        self.storage_class = config.get("storage_class", "STANDARD")

        if not self.bucket_name or not self.project_id:
            raise ValueError("bucket and project_id are required for GCS")

        # Initialize GCS client
        if config.get("credentials_json"):
            credentials = service_account.Credentials.from_service_account_file(
                config["credentials_json"]
            )
            self.client = storage.Client(
                project=self.project_id,
                credentials=credentials
            )
        elif config.get("credentials_dict"):
            credentials = service_account.Credentials.from_service_account_info(
                config["credentials_dict"]
            )
            self.client = storage.Client(
                project=self.project_id,
                credentials=credentials
            )
        else:
            # Use default credentials (from environment)
            self.client = storage.Client(project=self.project_id)

        self.bucket = None

    async def authenticate(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
        """Authenticate with GCS"""
        try:
            self.bucket = self.client.bucket(self.bucket_name)
            if not self.bucket.exists():
                raise StorageAuthenticationError(
                    f"GCS bucket not found: {self.bucket_name}",
                    details={"bucket": self.bucket_name}
                )
            self._authenticated = True
            logger.info(f"Successfully authenticated with GCS bucket: {self.bucket_name}")
            return True
        except gcp_exceptions.Forbidden as e:
            raise StorageAuthenticationError(
                f"Access denied to GCS bucket: {self.bucket_name}",
                details={"bucket": self.bucket_name, "error": str(e)}
            )
        except Exception as e:
            raise StorageConnectionError(
                f"Cannot connect to GCS: {str(e)}",
                details={"error": str(e)}
            )

    async def upload_file(
        self,
        local_path: str,
        remote_path: str,
        chunk_size: int = 64 * 1024 * 1024,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UploadResult:
        """Upload file to GCS"""
        start_time = time.time()
        local_file = Path(local_path)

        if not local_file.exists():
            raise InvalidPathError(f"Local file not found: {local_path}")

        remote_path = remote_path.lstrip('/')
        file_size = local_file.stat().st_size

        try:
            blob = self.bucket.blob(remote_path)

            if metadata:
                blob.metadata = metadata

            blob.upload_from_filename(str(local_file), timeout=300)

            duration = time.time() - start_time

            logger.info(
                f"Successfully uploaded {local_path} to GCS://{self.bucket_name}/{remote_path}",
                extra={"local_path": local_path, "remote_path": remote_path, "size_bytes": file_size}
            )

            return UploadResult(
                success=True,
                remote_path=f"gs://{self.bucket_name}/{remote_path}",
                bytes_uploaded=file_size,
                duration_seconds=duration,
                checksum=blob.md5_hash
            )

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"GCS upload failed: {str(e)}"
            logger.error(error_msg, extra={"error": str(e)})
            raise StorageUploadError(error_msg, details={"local_path": local_path, "error": str(e)})

    async def download_file(
        self,
        remote_path: str,
        local_path: str,
        chunk_size: int = 64 * 1024 * 1024,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> DownloadResult:
        """Download file from GCS"""
        start_time = time.time()
        local_file = Path(local_path)
        remote_path = remote_path.lstrip('/')

        local_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            blob = self.bucket.blob(remote_path)
            blob.download_to_filename(str(local_file), timeout=300)

            file_size = local_file.stat().st_size
            duration = time.time() - start_time

            logger.info(f"Successfully downloaded GCS://{self.bucket_name}/{remote_path} to {local_path}")

            return DownloadResult(
                success=True,
                local_path=local_path,
                bytes_downloaded=file_size,
                duration_seconds=duration,
                checksum=blob.md5_hash
            )

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"GCS download failed: {str(e)}"
            logger.error(error_msg, extra={"error": str(e)})
            raise StorageDownloadError(error_msg, details={"remote_path": remote_path, "error": str(e)})

    async def delete_file(self, remote_path: str) -> bool:
        """Delete file from GCS"""
        remote_path = remote_path.lstrip('/')
        try:
            blob = self.bucket.blob(remote_path)
            blob.delete()
            logger.info(f"Deleted GCS://{self.bucket_name}/{remote_path}")
            return True
        except Exception as e:
            raise StorageError(f"Failed to delete file: {str(e)}", details={"remote_path": remote_path})

    async def list_files(
        self,
        path: str = "",
        recursive: bool = False,
        max_results: Optional[int] = None
    ) -> List[FileInfo]:
        """List files in GCS bucket"""
        path = path.lstrip('/')
        file_list = []

        try:
            blobs = self.client.list_blobs(
                self.bucket_name,
                prefix=path,
                max_results=max_results,
                delimiter=None if recursive else '/'
            )

            for blob in blobs:
                if not blob.name.endswith('/'):  # Skip directory markers
                    file_list.append(FileInfo(
                        path=blob.name,
                        size_bytes=blob.size,
                        modified_time=blob.updated.replace(tzinfo=timezone.utc),
                        checksum=blob.md5_hash,
                        content_type=blob.content_type,
                        metadata=blob.metadata or {}
                    ))

            return file_list

        except Exception as e:
            raise StorageError(f"Failed to list files: {str(e)}", details={"path": path})

    async def file_exists(self, remote_path: str) -> bool:
        """Check if file exists in GCS"""
        remote_path = remote_path.lstrip('/')
        blob = self.bucket.blob(remote_path)
        return blob.exists()

    async def get_file_info(self, remote_path: str) -> Optional[FileInfo]:
        """Get file information from GCS"""
        remote_path = remote_path.lstrip('/')
        blob = self.bucket.blob(remote_path)

        if not blob.exists():
            return None

        blob.reload()

        return FileInfo(
            path=remote_path,
            size_bytes=blob.size,
            modified_time=blob.updated.replace(tzinfo=timezone.utc),
            checksum=blob.md5_hash,
            content_type=blob.content_type,
            metadata=blob.metadata or {}
        )

    async def check_space(self) -> StorageInfo:
        """Check GCS storage space"""
        try:
            total_size = 0
            for blob in self.client.list_blobs(self.bucket_name):
                total_size += blob.size

            return StorageInfo(
                total_bytes=100 * 1024 * 1024 * 1024 * 1024,  # 100TB virtual
                used_bytes=total_size,
                free_bytes=100 * 1024 * 1024 * 1024 * 1024 - total_size,
                provider="Google Cloud Storage",
                quota_exceeded=False
            )
        except Exception as e:
            raise StorageError(f"Failed to check storage: {str(e)}")

    async def create_directory(self, path: str) -> bool:
        """Create directory in GCS (creates marker object)"""
        path = path.lstrip('/').rstrip('/') + '/'
        blob = self.bucket.blob(path)
        blob.upload_from_string(b'')
        logger.info(f"Created directory marker: GCS://{self.bucket_name}/{path}")
        return True

    async def delete_directory(self, path: str, recursive: bool = False) -> bool:
        """Delete directory from GCS"""
        path = path.lstrip('/').rstrip('/') + '/'
        try:
            if recursive:
                blobs = self.client.list_blobs(self.bucket_name, prefix=path)
                for blob in blobs:
                    blob.delete()
                logger.info(f"Deleted directory recursively: GCS://{self.bucket_name}/{path}")
            else:
                blob = self.bucket.blob(path)
                blob.delete()
                logger.info(f"Deleted directory marker: GCS://{self.bucket_name}/{path}")
            return True
        except Exception as e:
            raise StorageError(f"Failed to delete directory: {str(e)}", details={"path": path})

#!/usr/bin/env python3
"""
Azure Blob Storage Provider
Production-grade Azure Blob Storage integration
"""

import time
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timezone

from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.core.exceptions import ResourceNotFoundError, AzureError

from .base import CloudStorageProvider, StorageInfo, UploadResult, FileInfo, DownloadResult
from ..core.exceptions import (
    StorageAuthenticationError, StorageUploadError, StorageDownloadError,
    StorageError, InvalidPathError, StorageConnectionError
)

logger = logging.getLogger(__name__)


class AzureBlobStorageProvider(CloudStorageProvider):
    """Azure Blob Storage provider with production-grade features"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Azure provider

        Required config:
            - account_name: Azure storage account name
            - container_name: Container name

        Optional config:
            - account_key: Account key
            - connection_string: Connection string
            - sas_token: SAS token
        """
        super().__init__(config)
        self.provider_name = "Azure Blob Storage"

        self.account_name = config.get("account_name")
        self.container_name = config.get("container_name")

        if not self.account_name or not self.container_name:
            raise ValueError("account_name and container_name are required for Azure")

        # Initialize blob service client
        if config.get("connection_string"):
            self.blob_service_client = BlobServiceClient.from_connection_string(
                config["connection_string"]
            )
        elif config.get("account_key"):
            account_url = f"https://{self.account_name}.blob.core.windows.net"
            self.blob_service_client = BlobServiceClient(
                account_url=account_url,
                credential=config["account_key"]
            )
        elif config.get("sas_token"):
            account_url = f"https://{self.account_name}.blob.core.windows.net"
            self.blob_service_client = BlobServiceClient(
                account_url=account_url,
                credential=config["sas_token"]
            )
        else:
            raise ValueError("One of connection_string, account_key, or sas_token is required")

        self.container_client = None

    async def authenticate(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
        """Authenticate with Azure Blob Storage"""
        try:
            self.container_client = self.blob_service_client.get_container_client(self.container_name)

            if not self.container_client.exists():
                raise StorageAuthenticationError(
                    f"Azure container not found: {self.container_name}",
                    details={"container": self.container_name}
                )

            self._authenticated = True
            logger.info(f"Successfully authenticated with Azure container: {self.container_name}")
            return True

        except Exception as e:
            raise StorageConnectionError(
                f"Cannot connect to Azure: {str(e)}",
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
        """Upload file to Azure Blob Storage"""
        start_time = time.time()
        local_file = Path(local_path)

        if not local_file.exists():
            raise InvalidPathError(f"Local file not found: {local_path}")

        remote_path = remote_path.lstrip('/')
        file_size = local_file.stat().st_size

        try:
            blob_client = self.container_client.get_blob_client(remote_path)

            with open(local_file, 'rb') as data:
                blob_client.upload_blob(
                    data,
                    overwrite=True,
                    metadata=metadata,
                    max_concurrency=4
                )

            duration = time.time() - start_time

            logger.info(
                f"Successfully uploaded {local_path} to Azure://{self.container_name}/{remote_path}",
                extra={"local_path": local_path, "remote_path": remote_path, "size_bytes": file_size}
            )

            return UploadResult(
                success=True,
                remote_path=f"azure://{self.container_name}/{remote_path}",
                bytes_uploaded=file_size,
                duration_seconds=duration
            )

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Azure upload failed: {str(e)}"
            logger.error(error_msg, extra={"error": str(e)})
            raise StorageUploadError(error_msg, details={"local_path": local_path, "error": str(e)})

    async def download_file(
        self,
        remote_path: str,
        local_path: str,
        chunk_size: int = 64 * 1024 * 1024,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> DownloadResult:
        """Download file from Azure Blob Storage"""
        start_time = time.time()
        local_file = Path(local_path)
        remote_path = remote_path.lstrip('/')

        local_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            blob_client = self.container_client.get_blob_client(remote_path)

            with open(local_file, 'wb') as download_file:
                download_stream = blob_client.download_blob()
                download_file.write(download_stream.readall())

            file_size = local_file.stat().st_size
            duration = time.time() - start_time

            logger.info(f"Successfully downloaded Azure://{self.container_name}/{remote_path} to {local_path}")

            return DownloadResult(
                success=True,
                local_path=local_path,
                bytes_downloaded=file_size,
                duration_seconds=duration
            )

        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Azure download failed: {str(e)}"
            logger.error(error_msg, extra={"error": str(e)})
            raise StorageDownloadError(error_msg, details={"remote_path": remote_path, "error": str(e)})

    async def delete_file(self, remote_path: str) -> bool:
        """Delete file from Azure Blob Storage"""
        remote_path = remote_path.lstrip('/')
        try:
            blob_client = self.container_client.get_blob_client(remote_path)
            blob_client.delete_blob()
            logger.info(f"Deleted Azure://{self.container_name}/{remote_path}")
            return True
        except Exception as e:
            raise StorageError(f"Failed to delete file: {str(e)}", details={"remote_path": remote_path})

    async def list_files(
        self,
        path: str = "",
        recursive: bool = False,
        max_results: Optional[int] = None
    ) -> List[FileInfo]:
        """List files in Azure container"""
        path = path.lstrip('/')
        file_list = []

        try:
            blob_list = self.container_client.list_blobs(name_starts_with=path)

            for blob in blob_list:
                if max_results and len(file_list) >= max_results:
                    break

                file_list.append(FileInfo(
                    path=blob.name,
                    size_bytes=blob.size,
                    modified_time=blob.last_modified.replace(tzinfo=timezone.utc),
                    content_type=blob.content_settings.content_type if blob.content_settings else None,
                    metadata=blob.metadata or {}
                ))

            return file_list

        except Exception as e:
            raise StorageError(f"Failed to list files: {str(e)}", details={"path": path})

    async def file_exists(self, remote_path: str) -> bool:
        """Check if file exists in Azure"""
        remote_path = remote_path.lstrip('/')
        try:
            blob_client = self.container_client.get_blob_client(remote_path)
            return blob_client.exists()
        except Exception:
            return False

    async def get_file_info(self, remote_path: str) -> Optional[FileInfo]:
        """Get file information from Azure"""
        remote_path = remote_path.lstrip('/')
        try:
            blob_client = self.container_client.get_blob_client(remote_path)
            props = blob_client.get_blob_properties()

            return FileInfo(
                path=remote_path,
                size_bytes=props.size,
                modified_time=props.last_modified.replace(tzinfo=timezone.utc),
                content_type=props.content_settings.content_type if props.content_settings else None,
                metadata=props.metadata or {}
            )

        except ResourceNotFoundError:
            return None
        except Exception as e:
            raise StorageError(f"Failed to get file info: {str(e)}", details={"remote_path": remote_path})

    async def check_space(self) -> StorageInfo:
        """Check Azure storage space"""
        try:
            total_size = 0
            for blob in self.container_client.list_blobs():
                total_size += blob.size

            return StorageInfo(
                total_bytes=100 * 1024 * 1024 * 1024 * 1024,  # 100TB virtual
                used_bytes=total_size,
                free_bytes=100 * 1024 * 1024 * 1024 * 1024 - total_size,
                provider="Azure Blob Storage",
                quota_exceeded=False
            )
        except Exception as e:
            raise StorageError(f"Failed to check storage: {str(e)}")

    async def create_directory(self, path: str) -> bool:
        """Create directory in Azure (creates marker blob)"""
        path = path.lstrip('/').rstrip('/') + '/'
        blob_client = self.container_client.get_blob_client(path)
        blob_client.upload_blob(b'', overwrite=True)
        logger.info(f"Created directory marker: Azure://{self.container_name}/{path}")
        return True

    async def delete_directory(self, path: str, recursive: bool = False) -> bool:
        """Delete directory from Azure"""
        path = path.lstrip('/').rstrip('/') + '/'
        try:
            if recursive:
                for blob in self.container_client.list_blobs(name_starts_with=path):
                    blob_client = self.container_client.get_blob_client(blob.name)
                    blob_client.delete_blob()
                logger.info(f"Deleted directory recursively: Azure://{self.container_name}/{path}")
            else:
                blob_client = self.container_client.get_blob_client(path)
                blob_client.delete_blob()
                logger.info(f"Deleted directory marker: Azure://{self.container_name}/{path}")
            return True
        except Exception as e:
            raise StorageError(f"Failed to delete directory: {str(e)}", details={"path": path})

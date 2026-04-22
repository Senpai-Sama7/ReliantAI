#!/usr/bin/env python3
"""
AWS S3 Storage Provider
Production-grade S3 integration with multipart uploads and retry logic
"""

import time
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError, BotoCoreError
from botocore.config import Config

from .base import (
    CloudStorageProvider, StorageInfo, UploadResult,
    FileInfo, DownloadResult
)
from ..core.exceptions import (
    StorageAuthenticationError, StorageUploadError,
    StorageDownloadError, StorageError, InvalidPathError,
    StorageConnectionError
)
from ..core.retry_logic import with_retry, RetryConfig, STANDARD_RETRY_CONFIG

logger = logging.getLogger(__name__)


class S3StorageProvider(CloudStorageProvider):
    """
    AWS S3 cloud storage provider

    Features:
    - Multipart uploads for large files
    - Server-side encryption
    - Versioning support
    - Retry logic with exponential backoff
    - Progress tracking
    - Checksum validation
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize S3 provider

        Required config:
            - bucket: S3 bucket name
            - region: AWS region (default: us-east-1)

        Optional config:
            - aws_access_key_id: AWS access key
            - aws_secret_access_key: AWS secret key
            - aws_session_token: AWS session token (for temporary credentials)
            - endpoint_url: Custom S3 endpoint (for S3-compatible services)
            - storage_class: Storage class (STANDARD, STANDARD_IA, GLACIER, etc.)
            - server_side_encryption: Encryption algorithm (AES256, aws:kms)
            - kms_key_id: KMS key ID (if using aws:kms)
            - versioning_enabled: Enable versioning
        """
        super().__init__(config)
        self.provider_name = "AWS S3"

        # S3 configuration
        self.bucket = config.get("bucket")
        if not self.bucket:
            raise ValueError("S3 bucket name is required")

        self.region = config.get("region", "us-east-1")
        self.storage_class = config.get("storage_class", "STANDARD")
        self.server_side_encryption = config.get("server_side_encryption")
        self.kms_key_id = config.get("kms_key_id")

        # Boto3 client configuration
        boto_config = Config(
            region_name=self.region,
            signature_version='s3v4',
            retries={
                'max_attempts': 3,
                'mode': 'adaptive'
            },
            max_pool_connections=50
        )

        # Initialize S3 client
        session_kwargs = {}
        if config.get("aws_access_key_id"):
            session_kwargs["aws_access_key_id"] = config["aws_access_key_id"]
        if config.get("aws_secret_access_key"):
            session_kwargs["aws_secret_access_key"] = config["aws_secret_access_key"]
        if config.get("aws_session_token"):
            session_kwargs["aws_session_token"] = config["aws_session_token"]

        self.session = boto3.Session(**session_kwargs)
        self.s3_client = self.session.client(
            's3',
            config=boto_config,
            endpoint_url=config.get("endpoint_url")
        )
        self.s3_resource = self.session.resource(
            's3',
            config=boto_config,
            endpoint_url=config.get("endpoint_url")
        )

        # Multipart upload configuration
        self.multipart_threshold = 100 * 1024 * 1024  # 100MB
        self.multipart_chunksize = 64 * 1024 * 1024   # 64MB per part

    async def authenticate(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
        """Authenticate with AWS S3"""
        try:
            # Test connection by checking if bucket exists
            self.s3_client.head_bucket(Bucket=self.bucket)
            self._authenticated = True
            logger.info(f"Successfully authenticated with S3 bucket: {self.bucket}")
            return True

        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            if error_code == '404':
                raise StorageAuthenticationError(
                    f"S3 bucket not found: {self.bucket}",
                    details={"bucket": self.bucket, "error_code": error_code}
                )
            elif error_code == '403':
                raise StorageAuthenticationError(
                    f"Access denied to S3 bucket: {self.bucket}",
                    details={"bucket": self.bucket, "error_code": error_code}
                )
            else:
                raise StorageAuthenticationError(
                    f"S3 authentication failed: {str(e)}",
                    details={"error": str(e), "error_code": error_code}
                )
        except BotoCoreError as e:
            raise StorageConnectionError(
                f"Cannot connect to S3: {str(e)}",
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
        """Upload file to S3 with multipart upload support"""
        start_time = time.time()
        local_file = Path(local_path)

        # Validate local file
        if not local_file.exists():
            raise InvalidPathError(f"Local file not found: {local_path}")
        if not local_file.is_file():
            raise InvalidPathError(f"Path is not a file: {local_path}")

        # Normalize remote path (remove leading slash)
        remote_path = remote_path.lstrip('/')

        file_size = local_file.stat().st_size

        try:
            # Calculate MD5 checksum
            md5_hash = hashlib.md5()
            with open(local_file, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    md5_hash.update(chunk)
            checksum = md5_hash.hexdigest()

            # Prepare upload arguments
            extra_args = {
                'StorageClass': self.storage_class
            }

            if self.server_side_encryption:
                extra_args['ServerSideEncryption'] = self.server_side_encryption
                if self.kms_key_id and self.server_side_encryption == 'aws:kms':
                    extra_args['SSEKMSKeyId'] = self.kms_key_id

            if metadata:
                extra_args['Metadata'] = {k: str(v) for k, v in metadata.items()}

            # Progress callback wrapper
            bytes_uploaded = [0]

            def upload_progress(bytes_amount):
                bytes_uploaded[0] += bytes_amount
                if progress_callback:
                    progress_callback(bytes_uploaded[0], file_size)

            # Upload file
            bucket = self.s3_resource.Bucket(self.bucket)

            bucket.upload_file(
                str(local_file),
                remote_path,
                ExtraArgs=extra_args,
                Callback=upload_progress
            )

            # Get version ID if versioning is enabled
            version_id = None
            try:
                obj = self.s3_client.head_object(Bucket=self.bucket, Key=remote_path)
                version_id = obj.get('VersionId')
            except ClientError:
                pass

            duration = time.time() - start_time

            logger.info(
                f"Successfully uploaded {local_path} to S3://{self.bucket}/{remote_path}",
                extra={
                    "local_path": local_path,
                    "remote_path": remote_path,
                    "size_bytes": file_size,
                    "duration_seconds": duration,
                    "checksum": checksum,
                    "version_id": version_id
                }
            )

            return UploadResult(
                success=True,
                remote_path=f"s3://{self.bucket}/{remote_path}",
                bytes_uploaded=file_size,
                duration_seconds=duration,
                checksum=checksum,
                version_id=version_id
            )

        except ClientError as e:
            duration = time.time() - start_time
            error_msg = f"S3 upload failed: {str(e)}"
            logger.error(error_msg, extra={"error": str(e), "local_path": local_path})

            return UploadResult(
                success=False,
                remote_path=f"s3://{self.bucket}/{remote_path}",
                bytes_uploaded=bytes_uploaded[0],
                duration_seconds=duration,
                error=error_msg
            )
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Upload failed: {str(e)}"
            logger.error(error_msg, extra={"error": str(e), "local_path": local_path})

            raise StorageUploadError(
                error_msg,
                details={"local_path": local_path, "remote_path": remote_path, "error": str(e)}
            )

    async def download_file(
        self,
        remote_path: str,
        local_path: str,
        chunk_size: int = 64 * 1024 * 1024,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> DownloadResult:
        """Download file from S3"""
        start_time = time.time()
        local_file = Path(local_path)

        # Normalize remote path
        remote_path = remote_path.lstrip('/')

        # Create parent directory if needed
        local_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Get file size first
            obj_info = self.s3_client.head_object(Bucket=self.bucket, Key=remote_path)
            file_size = obj_info['ContentLength']
            etag = obj_info.get('ETag', '').strip('"')

            # Progress callback wrapper
            bytes_downloaded = [0]

            def download_progress(bytes_amount):
                bytes_downloaded[0] += bytes_amount
                if progress_callback:
                    progress_callback(bytes_downloaded[0], file_size)

            # Download file
            bucket = self.s3_resource.Bucket(self.bucket)
            bucket.download_file(
                remote_path,
                str(local_file),
                Callback=download_progress
            )

            duration = time.time() - start_time

            logger.info(
                f"Successfully downloaded S3://{self.bucket}/{remote_path} to {local_path}",
                extra={
                    "remote_path": remote_path,
                    "local_path": local_path,
                    "size_bytes": file_size,
                    "duration_seconds": duration
                }
            )

            return DownloadResult(
                success=True,
                local_path=local_path,
                bytes_downloaded=file_size,
                duration_seconds=duration,
                checksum=etag
            )

        except ClientError as e:
            duration = time.time() - start_time
            error_msg = f"S3 download failed: {str(e)}"
            logger.error(error_msg, extra={"error": str(e), "remote_path": remote_path})

            return DownloadResult(
                success=False,
                local_path=local_path,
                bytes_downloaded=bytes_downloaded[0],
                duration_seconds=duration,
                error=error_msg
            )
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"Download failed: {str(e)}"
            logger.error(error_msg, extra={"error": str(e), "remote_path": remote_path})

            raise StorageDownloadError(
                error_msg,
                details={"remote_path": remote_path, "local_path": local_path, "error": str(e)}
            )

    async def delete_file(self, remote_path: str) -> bool:
        """Delete file from S3"""
        remote_path = remote_path.lstrip('/')

        try:
            self.s3_client.delete_object(Bucket=self.bucket, Key=remote_path)
            logger.info(f"Deleted S3://{self.bucket}/{remote_path}")
            return True

        except ClientError as e:
            logger.error(f"Failed to delete {remote_path}: {str(e)}")
            raise StorageError(
                f"Failed to delete file: {str(e)}",
                details={"remote_path": remote_path, "error": str(e)}
            )

    async def list_files(
        self,
        path: str = "",
        recursive: bool = False,
        max_results: Optional[int] = None
    ) -> List[FileInfo]:
        """List files in S3 bucket"""
        path = path.lstrip('/')
        file_list = []

        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.bucket,
                Prefix=path,
                Delimiter='' if recursive else '/'
            )

            count = 0
            for page in page_iterator:
                if 'Contents' in page:
                    for obj in page['Contents']:
                        if max_results and count >= max_results:
                            break

                        file_list.append(FileInfo(
                            path=obj['Key'],
                            size_bytes=obj['Size'],
                            modified_time=obj['LastModified'].replace(tzinfo=timezone.utc),
                            checksum=obj.get('ETag', '').strip('"')
                        ))
                        count += 1

                if max_results and count >= max_results:
                    break

            return file_list

        except ClientError as e:
            logger.error(f"Failed to list files in {path}: {str(e)}")
            raise StorageError(
                f"Failed to list files: {str(e)}",
                details={"path": path, "error": str(e)}
            )

    async def file_exists(self, remote_path: str) -> bool:
        """Check if file exists in S3"""
        remote_path = remote_path.lstrip('/')

        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=remote_path)
            return True
        except ClientError as e:
            if e.response.get('Error', {}).get('Code') == '404':
                return False
            raise

    async def get_file_info(self, remote_path: str) -> Optional[FileInfo]:
        """Get file information from S3"""
        remote_path = remote_path.lstrip('/')

        try:
            obj = self.s3_client.head_object(Bucket=self.bucket, Key=remote_path)

            return FileInfo(
                path=remote_path,
                size_bytes=obj['ContentLength'],
                modified_time=obj['LastModified'].replace(tzinfo=timezone.utc),
                checksum=obj.get('ETag', '').strip('"'),
                content_type=obj.get('ContentType'),
                metadata=obj.get('Metadata', {})
            )

        except ClientError as e:
            if e.response.get('Error', {}).get('Code') == '404':
                return None
            raise StorageError(
                f"Failed to get file info: {str(e)}",
                details={"remote_path": remote_path, "error": str(e)}
            )

    async def check_space(self) -> StorageInfo:
        """
        Check S3 storage space
        Note: S3 doesn't have traditional quota limits, returns estimated usage
        """
        try:
            # Calculate total size of objects in bucket
            total_size = 0
            paginator = self.s3_client.get_paginator('list_objects_v2')

            for page in paginator.paginate(Bucket=self.bucket):
                if 'Contents' in page:
                    total_size += sum(obj['Size'] for obj in page['Contents'])

            # S3 doesn't have a fixed quota (effectively unlimited)
            return StorageInfo(
                total_bytes=100 * 1024 * 1024 * 1024 * 1024,  # 100TB "virtual" total
                used_bytes=total_size,
                free_bytes=100 * 1024 * 1024 * 1024 * 1024 - total_size,
                provider="AWS S3",
                quota_exceeded=False
            )

        except ClientError as e:
            logger.error(f"Failed to check S3 storage: {str(e)}")
            raise StorageError(
                f"Failed to check storage: {str(e)}",
                details={"error": str(e)}
            )

    async def create_directory(self, path: str) -> bool:
        """
        Create directory in S3 (creates a marker object)
        Note: S3 doesn't have true directories, but we create a marker
        """
        path = path.lstrip('/').rstrip('/') + '/'

        try:
            self.s3_client.put_object(Bucket=self.bucket, Key=path, Body=b'')
            logger.info(f"Created directory marker: S3://{self.bucket}/{path}")
            return True

        except ClientError as e:
            logger.error(f"Failed to create directory {path}: {str(e)}")
            raise StorageError(
                f"Failed to create directory: {str(e)}",
                details={"path": path, "error": str(e)}
            )

    async def delete_directory(self, path: str, recursive: bool = False) -> bool:
        """Delete directory from S3"""
        path = path.lstrip('/').rstrip('/') + '/'

        try:
            if recursive:
                # Delete all objects with this prefix
                objects_to_delete = []
                paginator = self.s3_client.get_paginator('list_objects_v2')

                for page in paginator.paginate(Bucket=self.bucket, Prefix=path):
                    if 'Contents' in page:
                        objects_to_delete.extend([{'Key': obj['Key']} for obj in page['Contents']])

                if objects_to_delete:
                    # Delete in batches of 1000 (S3 limit)
                    for i in range(0, len(objects_to_delete), 1000):
                        batch = objects_to_delete[i:i+1000]
                        self.s3_client.delete_objects(
                            Bucket=self.bucket,
                            Delete={'Objects': batch}
                        )

                logger.info(f"Deleted directory recursively: S3://{self.bucket}/{path}")
            else:
                # Just delete the directory marker
                self.s3_client.delete_object(Bucket=self.bucket, Key=path)
                logger.info(f"Deleted directory marker: S3://{self.bucket}/{path}")

            return True

        except ClientError as e:
            logger.error(f"Failed to delete directory {path}: {str(e)}")
            raise StorageError(
                f"Failed to delete directory: {str(e)}",
                details={"path": path, "error": str(e)}
            )

"""
Data upload, listing, and retrieval endpoints.
"""
import asyncio
from datetime import datetime, timezone
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, cast
import uuid

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Query, Depends, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.middleware.auth import get_current_user_optional
from src.config import get_settings
from src.core.event_bus import publish_event
from src.core.database import get_db
from src.core.datasets import build_upload_path, inspect_dataset
from src.models.analytics_models import DatasetResponse
from src.models.data_models import Dataset
from src.utils.logger import get_logger
from src.utils.metrics import REQUESTS, LATENCY

router = APIRouter()
logger = get_logger()
settings = get_settings()

# Allowed file extensions and max file size
ALLOWED_EXTENSIONS = {".csv", ".json", ".xlsx", ".parquet"}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

@router.post("/upload-data", response_model=DatasetResponse)
async def upload_data(
    response: Response,
    file: UploadFile = File(..., description="Data file to upload (CSV, JSON, XLSX, or Parquet)"),
    name: Optional[str] = Query(None, description="Dataset name"),
    description: Optional[str] = Query(None, description="Dataset description"),
    db: AsyncSession = Depends(get_db),
    user: Optional[Dict[str, Any]] = Depends(get_current_user_optional),
) -> DatasetResponse:
    """Upload a CSV, JSON, XLSX, or Parquet file for analytics processing."""
    start_time = time.time()
    stored_path: Optional[Path] = None
    
    try:
        # Validate file extension
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Filename is required"
            )
        
        file_ext = "." + file.filename.split(".")[-1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only {', '.join(ALLOWED_EXTENSIONS)} files are accepted."
            )
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Validate file size
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / (1024*1024)}MB"
            )
        
        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File is empty"
            )
        
        # Generate dataset ID
        dataset_id = f"ds-{uuid.uuid4().hex[:12]}"

        upload_root = Path(settings.UPLOADS_DIR)
        await asyncio.to_thread(upload_root.mkdir, parents=True, exist_ok=True)
        stored_path = build_upload_path(upload_root, dataset_id, file.filename)
        await asyncio.to_thread(stored_path.write_bytes, content)

        try:
            inspection = inspect_dataset(file.filename, content)
        except Exception as exc:
            await _cleanup_file(stored_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to parse uploaded file: {exc}",
            ) from exc

        created_by = _get_created_by(user)
        dataset = Dataset(
            dataset_id=dataset_id,
            name=name or Path(file.filename).stem,
            description=description,
            file_path=str(stored_path),
            file_type=inspection.file_type,
            created_by=created_by,
            status="uploaded",
            metadata_={
                "original_filename": file.filename,
                "columns": inspection.columns,
            },
            row_count=inspection.row_count,
            column_count=inspection.column_count,
            file_size=file_size,
        )
        db.add(dataset)
        await db.commit()
        await db.refresh(dataset)

        event_info = await publish_event(
            "document.processed",
            {
                "dataset_id": dataset_id,
                "name": cast(str, dataset.name),
                "file_type": inspection.file_type,
                "row_count": inspection.row_count,
                "column_count": inspection.column_count,
                "created_by": created_by,
            },
            correlation_id=dataset_id,
            tenant_id=_get_tenant_id(user),
            source_service="bap-upload",
        )
        if event_info is not None and response is not None:
            response.headers["X-EventBus-EventId"] = event_info["event_id"]
            response.headers["X-EventBus-Channel"] = event_info["channel"]

        logger.info(
            f"Uploaded file {file.filename} with size {file_size} bytes as dataset {dataset_id}",
            dataset_id=dataset_id,
            row_count=inspection.row_count,
            column_count=inspection.column_count,
            file_type=inspection.file_type,
            created_by=created_by,
        )

        dataset_response = _to_dataset_response(dataset)
        
        REQUESTS.labels(method="POST", endpoint="/api/data/upload-data", status="200").inc()
        LATENCY.labels(method="POST", endpoint="/api/data/upload-data").observe(time.time() - start_time)
        
        return dataset_response
        
    except HTTPException as exc:
        REQUESTS.labels(method="POST", endpoint="/api/data/upload-data", status=str(exc.status_code)).inc()
        raise
    except Exception as e:
        logger.error(f"Failed to upload file: {e}")
        if stored_path is not None:
            await _cleanup_file(stored_path)
        REQUESTS.labels(method="POST", endpoint="/api/data/upload-data", status="500").inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )

@router.get("/datasets", response_model=List[DatasetResponse])
async def list_datasets(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: AsyncSession = Depends(get_db),
) -> List[DatasetResponse]:
    """List all datasets with pagination."""
    try:
        result = await db.execute(
            select(Dataset)
            .order_by(Dataset.created_at.desc(), Dataset.id.desc())
            .offset(skip)
            .limit(limit)
        )
        datasets = [_to_dataset_response(dataset) for dataset in result.scalars().all()]

        logger.info(f"Listed {len(datasets)} datasets")
        return datasets
        
    except Exception as e:
        logger.error(f"Failed to list datasets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list datasets: {str(e)}"
        )

@router.get("/datasets/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
) -> DatasetResponse:
    """Get details of a specific dataset."""
    try:
        result = await db.execute(select(Dataset).where(Dataset.dataset_id == dataset_id))
        dataset = result.scalar_one_or_none()
        if dataset is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset {dataset_id} not found"
            )
        return _to_dataset_response(dataset)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get dataset {dataset_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dataset: {str(e)}"
        )


@router.delete("/datasets/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    dataset_id: str,
    db: AsyncSession = Depends(get_db),
) -> Response:
    """Delete a dataset record and its stored file."""
    try:
        result = await db.execute(select(Dataset).where(Dataset.dataset_id == dataset_id))
        dataset = result.scalar_one_or_none()
        if dataset is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset {dataset_id} not found"
            )

        file_path = cast(Optional[str], dataset.file_path)
        if file_path:
            await _cleanup_file(Path(file_path))

        await db.delete(dataset)
        await db.commit()
        logger.info(f"Deleted dataset {dataset_id}")
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete dataset {dataset_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete dataset: {str(e)}"
        )


def _to_dataset_response(dataset: Dataset) -> DatasetResponse:
    created_at = cast(Optional[datetime], dataset.created_at) or datetime.now(timezone.utc)
    return DatasetResponse(
        dataset_id=cast(str, dataset.dataset_id),
        name=cast(str, dataset.name),
        description=cast(Optional[str], dataset.description),
        status=cast(str, dataset.status),
        row_count=cast(int, dataset.row_count),
        column_count=cast(int, dataset.column_count),
        file_size=cast(int, dataset.file_size),
        created_at=created_at,
        created_by=cast(str, dataset.created_by),
    )


def _get_created_by(user: Optional[Dict[str, Any]]) -> str:
    if not user:
        return "system"

    for key in ("username", "sub", "user_id", "email"):
        value = user.get(key)
        if isinstance(value, str) and value:
            return value

    return "system"


def _get_tenant_id(user: Optional[Dict[str, Any]]) -> str | None:
    if not user:
        return None

    tenant_id = user.get("tenant_id")
    return tenant_id if isinstance(tenant_id, str) and tenant_id else None


async def _cleanup_file(path: Path) -> None:
    if path.exists():
        await asyncio.to_thread(path.unlink)

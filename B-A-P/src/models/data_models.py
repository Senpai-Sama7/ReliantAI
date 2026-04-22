"""
Data models for database entities and ORM.
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, JSON
from sqlalchemy.sql import func
from src.core.database import Base

class Dataset(Base):  # type: ignore[misc]
    """Dataset entity representing uploaded data."""
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(String(128), unique=True, index=True, nullable=False)
    name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    file_path = Column(String(1024), nullable=False)
    file_type = Column(String(32), nullable=False)
    source = Column(String(256), nullable=True)
    created_by = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    status = Column(String(50), default="uploaded")
    metadata_ = Column("metadata", JSON, default=dict)
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    file_size = Column(Integer, default=0)

class ETLJob(Base):  # type: ignore[misc]
    """ETL job execution tracking."""
    __tablename__ = "etl_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(128), unique=True, index=True, nullable=False)
    dataset_id = Column(String(128), index=True, nullable=False)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    parameters = Column(JSON, default=dict)
    result = Column(JSON, default=dict)
    created_by = Column(String(128), nullable=False)


class ProcessedDataset(Base):  # type: ignore[misc]
    """Processed dataset artifacts produced by the ETL pipeline."""
    __tablename__ = "processed_datasets"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(String(128), unique=True, index=True, nullable=False)
    source_job_id = Column(String(128), index=True, nullable=False)
    row_count = Column(Integer, default=0)
    column_count = Column(Integer, default=0)
    schema_ = Column("schema", JSON, default=dict)
    summary = Column(JSON, default=dict)
    records = Column(JSON, default=list)
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(String(128), nullable=False)


class AIInsight(Base):  # type: ignore[misc]
    """AI-generated insights."""
    __tablename__ = "ai_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    insight_id = Column(String(128), unique=True, index=True, nullable=False)
    dataset_id = Column(String(128), index=True, nullable=False)
    insight_type = Column(String(50), nullable=False)  # summary, forecast, anomaly, etc.
    content = Column(Text, nullable=False)
    confidence = Column(Float, default=0.0)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(String(128), nullable=False)

class User(Base):  # type: ignore[misc]
    """User entity for authentication."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(128), unique=True, index=True, nullable=False)
    email = Column(String(256), unique=True, index=True, nullable=False)
    full_name = Column(String(256), nullable=True)
    hashed_password = Column(String(256), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)

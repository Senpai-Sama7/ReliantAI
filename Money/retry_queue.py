"""
Retry Queue + Dead Letter Queue for HVAC Dispatch
Handles transient failures with exponential backoff.
"""

import time
import threading
import logging
from dataclasses import dataclass, asdict
from typing import Optional
from datetime import datetime, timezone, timedelta
from enum import Enum

from database import get_pool

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    DLQ = "dlq"  # Dead letter queue - max retries exceeded


@dataclass
class DispatchJob:
    job_id: str
    message: str
    outdoor_temp: int
    phone: Optional[str]
    attempt: int = 0
    max_attempts: int = 3
    status: str = "pending"
    created_at: str = ""
    next_attempt_at: str = ""
    error: Optional[str] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()
        if not self.next_attempt_at:
            self.next_attempt_at = self.created_at
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "DispatchJob":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class RetryQueue:
    """
    PostgreSQL-backed retry queue with dead letter queue.
    
    Features:
    - Exponential backoff (2^attempt * base_delay)
    - Max retry limit with automatic DLQ
    - Concurrent-safe with row-level locking
    - Automatic cleanup of old jobs
    """
    
    def __init__(
        self,
        base_delay_seconds: float = 5.0,
        max_delay_seconds: float = 300.0,
        cleanup_interval_hours: int = 24
    ):
        self.base_delay = base_delay_seconds
        self.max_delay = max_delay_seconds
        self.cleanup_interval = cleanup_interval_hours
        self._lock = threading.Lock()
        self._ensure_tables()
    
    def _ensure_tables(self):
        """Create retry queue and DLQ tables if not exist."""
        pool = get_pool()
        conn = pool.getconn()
        try:
            with conn.cursor() as cur:
                # Main retry queue
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS retry_queue (
                        job_id TEXT PRIMARY KEY,
                        message TEXT NOT NULL,
                        outdoor_temp INTEGER,
                        phone TEXT,
                        attempt INTEGER DEFAULT 0,
                        max_attempts INTEGER DEFAULT 3,
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT NOW(),
                        next_attempt_at TIMESTAMP DEFAULT NOW(),
                        error TEXT,
                        updated_at TIMESTAMP DEFAULT NOW()
                    )
                """)
                
                # Dead letter queue
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS dead_letter_queue (
                        job_id TEXT PRIMARY KEY,
                        message TEXT NOT NULL,
                        outdoor_temp INTEGER,
                        phone TEXT,
                        attempt INTEGER,
                        max_attempts INTEGER,
                        error TEXT,
                        failed_at TIMESTAMP DEFAULT NOW(),
                        original_created_at TIMESTAMP
                    )
                """)
                
                # Indexes for performance
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_retry_queue_status 
                    ON retry_queue(status, next_attempt_at)
                """)
                cur.execute("""
                    CREATE INDEX IF NOT EXISTS idx_retry_queue_pending 
                    ON retry_queue(status) WHERE status = 'pending'
                """)
                
                conn.commit()
        finally:
            pool.putconn(conn)
    
    def enqueue(self, job: DispatchJob) -> str:
        """Add a job to the retry queue."""
        pool = get_pool()
        conn = pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO retry_queue 
                    (job_id, message, outdoor_temp, phone, attempt, max_attempts, 
                     status, created_at, next_attempt_at, error)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (job_id) DO UPDATE SET
                        attempt = EXCLUDED.attempt,
                        status = EXCLUDED.status,
                        next_attempt_at = EXCLUDED.next_attempt_at,
                        error = EXCLUDED.error,
                        updated_at = NOW()
                """, (
                    job.job_id, job.message, job.outdoor_temp, job.phone,
                    job.attempt, job.max_attempts, job.status,
                    job.created_at, job.next_attempt_at, job.error
                ))
                conn.commit()
                logger.info(f"Enqueued job {job.job_id}, attempt {job.attempt}")
                return job.job_id
        finally:
            pool.putconn(conn)
    
    def dequeue(self) -> Optional[DispatchJob]:
        """Get next pending job with row locking."""
        pool = get_pool()
        conn = pool.getconn()
        try:
            with conn.cursor() as cur:
                # Lock and fetch next pending job
                cur.execute("""
                    SELECT job_id, message, outdoor_temp, phone, attempt, 
                           max_attempts, status, created_at, next_attempt_at, error
                    FROM retry_queue
                    WHERE status = 'pending' 
                      AND next_attempt_at <= NOW()
                    ORDER BY next_attempt_at
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                """)
                row = cur.fetchone()
                
                if not row:
                    return None
                
                job = DispatchJob(
                    job_id=row[0], message=row[1], outdoor_temp=row[2],
                    phone=row[3], attempt=row[4], max_attempts=row[5],
                    status=row[6], created_at=row[7], next_attempt_at=row[8],
                    error=row[9]
                )
                
                # Mark as processing
                cur.execute("""
                    UPDATE retry_queue 
                    SET status = 'processing', updated_at = NOW()
                    WHERE job_id = %s
                """, (job.job_id,))
                conn.commit()
                
                return job
        finally:
            pool.putconn(conn)
    
    def mark_success(self, job_id: str):
        """Mark job as successfully completed."""
        pool = get_pool()
        conn = pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM retry_queue 
                    WHERE job_id = %s
                """, (job_id,))
                conn.commit()
                logger.info(f"Job {job_id} completed successfully")
        finally:
            pool.putconn(conn)
    
    def mark_failure(self, job: DispatchJob, error: str) -> bool:
        """
        Mark job as failed. Returns True if moved to DLQ, False if retry scheduled.
        """
        job.attempt += 1
        job.error = error
        
        if job.attempt >= job.max_attempts:
            # Move to dead letter queue
            return self._move_to_dlq(job)
        
        # Schedule retry with exponential backoff
        delay = min(self.base_delay * (2 ** job.attempt), self.max_delay)
        next_attempt = datetime.now(timezone.utc) + timedelta(seconds=int(delay))
        job.next_attempt_at = next_attempt.isoformat()
        job.status = "pending"
        
        self.enqueue(job)
        logger.warning(f"Job {job.job_id} failed (attempt {job.attempt}), retry in {delay}s")
        return False
    
    def _move_to_dlq(self, job: DispatchJob) -> bool:
        """Move job to dead letter queue."""
        pool = get_pool()
        conn = pool.getconn()
        try:
            with conn.cursor() as cur:
                # Insert into DLQ
                cur.execute("""
                    INSERT INTO dead_letter_queue
                    (job_id, message, outdoor_temp, phone, attempt, max_attempts,
                     error, original_created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    job.job_id, job.message, job.outdoor_temp, job.phone,
                    job.attempt, job.max_attempts, job.error, job.created_at
                ))
                
                # Remove from retry queue
                cur.execute("DELETE FROM retry_queue WHERE job_id = %s", (job.job_id,))
                conn.commit()
                
                logger.error(f"Job {job.job_id} moved to DLQ after {job.attempt} attempts")
                return True
        finally:
            pool.putconn(conn)
    
    def get_stats(self) -> dict:
        """Get queue statistics."""
        pool = get_pool()
        conn = pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT status, COUNT(*) 
                    FROM retry_queue 
                    GROUP BY status
                """)
                queue_stats = dict(cur.fetchall())
                
                cur.execute("SELECT COUNT(*) FROM dead_letter_queue")
                dlq_count = cur.fetchone()[0]
                
                return {
                    "retry_queue": queue_stats,
                    "dead_letter_queue": dlq_count,
                    "total_pending": queue_stats.get('pending', 0) + queue_stats.get('processing', 0)
                }
        finally:
            pool.putconn(conn)
    
    def get_dlq_jobs(self, limit: int = 100) -> list:
        """Get jobs from dead letter queue for analysis/reprocessing."""
        pool = get_pool()
        conn = pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT job_id, message, outdoor_temp, phone, attempt, 
                           error, failed_at, original_created_at
                    FROM dead_letter_queue
                    ORDER BY failed_at DESC
                    LIMIT %s
                """, (limit,))
                
                jobs = []
                for row in cur.fetchall():
                    jobs.append({
                        "job_id": row[0],
                        "message": row[1],
                        "outdoor_temp": row[2],
                        "phone": row[3],
                        "attempt": row[4],
                        "error": row[5],
                        "failed_at": row[6],
                        "original_created_at": row[7]
                    })
                return jobs
        finally:
            pool.putconn(conn)
    
    def reprocess_dlq_job(self, job_id: str) -> bool:
        """Reprocess a job from DLQ (admin manual retry)."""
        pool = get_pool()
        conn = pool.getconn()
        try:
            with conn.cursor() as cur:
                # Get job from DLQ
                cur.execute("""
                    SELECT job_id, message, outdoor_temp, phone, attempt, max_attempts
                    FROM dead_letter_queue WHERE job_id = %s
                """, (job_id,))
                row = cur.fetchone()
                
                if not row:
                    return False
                
                # Create new job with reset attempt count
                job = DispatchJob(
                    job_id=f"{row[0]}_retry_{int(time.time())}",
                    message=row[1],
                    outdoor_temp=row[2],
                    phone=row[3],
                    attempt=0,
                    max_attempts=row[5]
                )
                
                self.enqueue(job)
                
                # Remove from DLQ
                cur.execute("DELETE FROM dead_letter_queue WHERE job_id = %s", (job_id,))
                conn.commit()
                
                logger.info(f"Reprocessed DLQ job {job_id} as {job.job_id}")
                return True
        finally:
            pool.putconn(conn)


# Singleton instance
_retry_queue: Optional[RetryQueue] = None
_queue_lock = threading.Lock()

def get_retry_queue() -> RetryQueue:
    """Get or create retry queue singleton."""
    global _retry_queue
    if _retry_queue is None:
        with _queue_lock:
            if _retry_queue is None:
                _retry_queue = RetryQueue()
    return _retry_queue

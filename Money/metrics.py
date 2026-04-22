import os
import time
from functools import wraps
from typing import Callable, Any
from fastapi.responses import Response

try:
    from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
except ImportError:
    Counter = None
    Histogram = None
    generate_latest = None
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"

if Counter and Histogram:
    GEMINI_AGENT_EXECUTION_TIME = Histogram(
        'gemini_agent_execution_seconds',
        'Time spent executing Gemini agent chains',
        ['agent_name', 'status']
    )
    
    GEMINI_TOKEN_USAGE = Counter(
        'gemini_tokens_total',
        'Total Gemini tokens used',
        ['token_type', 'model']
    )
    
    DISPATCH_JOB_DURATION = Histogram(
        'dispatch_job_execution_seconds',
        'Time spent executing dispatch jobs',
        ['status']
    )
else:
    GEMINI_AGENT_EXECUTION_TIME = None
    GEMINI_TOKEN_USAGE = None
    DISPATCH_JOB_DURATION = None

def track_agent_execution(agent_name: str):
    """Decorator to track Gemini agent execution time and status."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if not GEMINI_AGENT_EXECUTION_TIME:
                return func(*args, **kwargs)
                
            start_time = time.time()
            status = "success"
            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                GEMINI_AGENT_EXECUTION_TIME.labels(
                    agent_name=agent_name, 
                    status=status
                ).observe(duration)
        return wrapper
    return decorator

def get_metrics_response():
    """Returns the Prometheus metrics payload."""
    if generate_latest:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
    from fastapi import HTTPException
    raise HTTPException(status_code=503, detail="Prometheus metrics unavailable")

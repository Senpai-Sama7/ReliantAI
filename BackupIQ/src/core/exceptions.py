#!/usr/bin/env python3
"""
Custom Exception Hierarchy for BackupIQ
FAANG-grade error handling with specific exception types
"""

from typing import Optional, Dict, Any


class BackupIQException(Exception):
    """Base exception for all BackupIQ errors"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/API responses"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


# Configuration Errors
class ConfigurationError(BackupIQException):
    """Configuration-related errors"""
    pass


class ConfigNotFoundError(ConfigurationError):
    """Configuration file not found"""
    pass


class ConfigValidationError(ConfigurationError):
    """Configuration validation failed"""
    pass


class EnvironmentVariableError(ConfigurationError):
    """Required environment variable not set"""
    pass


# Storage Errors
class StorageError(BackupIQException):
    """Cloud storage errors"""
    pass


class StorageAuthenticationError(StorageError):
    """Authentication with storage provider failed"""
    pass


class StorageQuotaExceededError(StorageError):
    """Storage quota exceeded"""
    pass


class StorageUploadError(StorageError):
    """File upload failed"""
    pass


class StorageDownloadError(StorageError):
    """File download failed"""
    pass


class StorageConnectionError(StorageError):
    """Cannot connect to storage provider"""
    pass


# Authentication Errors
class AuthenticationError(BackupIQException):
    """Authentication failures"""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Invalid username/password or API key"""
    pass


class TokenExpiredError(AuthenticationError):
    """JWT token has expired"""
    pass


class TokenInvalidError(AuthenticationError):
    """JWT token is invalid"""
    pass


class PermissionDeniedError(AuthenticationError):
    """User does not have required permissions"""
    pass


# Validation Errors
class ValidationError(BackupIQException):
    """Input validation errors"""
    pass


class InvalidPathError(ValidationError):
    """Invalid file or directory path"""
    pass


class InvalidParameterError(ValidationError):
    """Invalid parameter value"""
    pass


class FileTooLargeError(ValidationError):
    """File exceeds maximum size limit"""
    pass


# Resource Errors
class ResourceError(BackupIQException):
    """Resource-related errors"""
    pass


class ResourceExhaustedError(ResourceError):
    """Resource limit exceeded (memory, CPU, disk)"""
    pass


class DiskSpaceError(ResourceError):
    """Insufficient disk space"""
    pass


class MemoryError(ResourceError):
    """Insufficient memory"""
    pass


# Database Errors
class DatabaseError(BackupIQException):
    """Database-related errors"""
    pass


class DatabaseConnectionError(DatabaseError):
    """Cannot connect to database"""
    pass


class QueryError(DatabaseError):
    """Database query failed"""
    pass


class TransactionError(DatabaseError):
    """Database transaction failed"""
    pass


# Semantic Analysis Errors
class SemanticAnalysisError(BackupIQException):
    """Semantic analysis errors"""
    pass


class FileTypeUnknownError(SemanticAnalysisError):
    """Cannot determine file type"""
    pass


class ParsingError(SemanticAnalysisError):
    """Cannot parse file content"""
    pass


# Knowledge Graph Errors
class KnowledgeGraphError(BackupIQException):
    """Knowledge graph errors"""
    pass


class GraphConnectionError(KnowledgeGraphError):
    """Cannot connect to graph database"""
    pass


class GraphQueryError(KnowledgeGraphError):
    """Graph query failed"""
    pass


# Backup Operation Errors
class BackupOperationError(BackupIQException):
    """Backup operation errors"""
    pass


class FileDiscoveryError(BackupOperationError):
    """File discovery failed"""
    pass


class BackupInProgressError(BackupOperationError):
    """Backup operation already in progress"""
    pass


class BackupCancelledError(BackupOperationError):
    """Backup operation was cancelled"""
    pass


# Circuit Breaker Errors
class CircuitBreakerError(BackupIQException):
    """Circuit breaker errors"""
    pass


class CircuitBreakerOpenError(CircuitBreakerError):
    """Circuit breaker is open, rejecting requests"""
    pass


# Rate Limiting Errors
class RateLimitError(BackupIQException):
    """Rate limiting errors"""
    pass


class RateLimitExceededError(RateLimitError):
    """Rate limit exceeded"""
    pass


# API Errors
class APIError(BackupIQException):
    """API-related errors"""
    pass


class EndpointNotFoundError(APIError):
    """API endpoint not found"""
    pass


class InvalidRequestError(APIError):
    """Invalid API request"""
    pass


class ServiceUnavailableError(APIError):
    """Service temporarily unavailable"""
    pass


# Monitoring Errors
class MonitoringError(BackupIQException):
    """Monitoring and observability errors"""
    pass


class MetricsCollectionError(MonitoringError):
    """Metrics collection failed"""
    pass


class HealthCheckError(MonitoringError):
    """Health check failed"""
    pass


def error_to_http_status(error: BackupIQException) -> int:
    """Map exception types to HTTP status codes"""
    error_map = {
        # 400 Bad Request
        ValidationError: 400,
        InvalidPathError: 400,
        InvalidParameterError: 400,
        FileTooLargeError: 400,
        InvalidRequestError: 400,
        ConfigValidationError: 400,

        # 401 Unauthorized
        AuthenticationError: 401,
        InvalidCredentialsError: 401,
        TokenExpiredError: 401,
        TokenInvalidError: 401,

        # 403 Forbidden
        PermissionDeniedError: 403,

        # 404 Not Found
        ConfigNotFoundError: 404,
        EndpointNotFoundError: 404,

        # 409 Conflict
        BackupInProgressError: 409,

        # 429 Too Many Requests
        RateLimitExceededError: 429,

        # 500 Internal Server Error
        StorageError: 500,
        DatabaseError: 500,
        SemanticAnalysisError: 500,
        KnowledgeGraphError: 500,
        BackupOperationError: 500,

        # 502 Bad Gateway
        StorageConnectionError: 502,
        DatabaseConnectionError: 502,
        GraphConnectionError: 502,

        # 503 Service Unavailable
        CircuitBreakerOpenError: 503,
        ServiceUnavailableError: 503,
        ResourceExhaustedError: 503,

        # 507 Insufficient Storage
        StorageQuotaExceededError: 507,
        DiskSpaceError: 507,
    }

    return error_map.get(type(error), 500)

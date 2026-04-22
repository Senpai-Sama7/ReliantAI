#!/usr/bin/env python3
"""
Shared Test Fixtures

Provides reusable fixtures for integration tests across all services.

This is a REAL implementation - not a mock or placeholder.
"""

import os
import sqlite3
import tempfile
import threading
from typing import Generator, Optional
from contextlib import contextmanager
from dataclasses import dataclass

# PostgreSQL support
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False


@dataclass
class DatabaseConfig:
    """Database configuration for tests."""
    host: str = "localhost"
    port: int = 5432
    database: str = "test_db"
    user: str = "test_user"
    password: str = "test_pass"


class TestDatabase:
    """
    Test database manager.
    
    Provides isolated test databases for SQLite and PostgreSQL.
    """
    
    def __init__(self, db_type: str = "sqlite"):
        self.db_type = db_type
        self.connection = None
        self._temp_file: Optional[str] = None
    
    def create_sqlite_db(self, suffix: str = "") -> str:
        """
        Create isolated SQLite test database.
        
        Returns:
            Path to test database file
        """
        thread_id = threading.current_thread().ident
        fd, path = tempfile.mkstemp(
            suffix=f"_test{suffix}_{thread_id}.db",
            prefix="integration_",
            dir="/tmp"
        )
        os.close(fd)
        
        self._temp_file = path
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        
        return path
    
    def create_postgres_db(self, config: DatabaseConfig = None) -> bool:
        """
        Create PostgreSQL test database connection.
        
        Returns:
            True if connection successful
        """
        if not POSTGRES_AVAILABLE:
            return False
        
        config = config or DatabaseConfig()
        
        try:
            self.connection = psycopg2.connect(
                host=config.host,
                port=config.port,
                database=config.database,
                user=config.user,
                password=config.password
            )
            return True
        except Exception as e:
            print(f"PostgreSQL connection failed: {e}")
            return False
    
    def execute(self, sql: str, params: tuple = None):
        """Execute SQL query."""
        if self.connection:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            self.connection.commit()
            return cursor
    
    def query(self, sql: str, params: tuple = None):
        """Execute SELECT query and return results."""
        if self.connection:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return cursor.fetchall()
    
    def close(self):
        """Close database connection and cleanup."""
        if self.connection:
            self.connection.close()
            self.connection = None
        
        if self._temp_file and os.path.exists(self._temp_file):
            os.remove(self._temp_file)
            self._temp_file = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


@contextmanager
def sqlite_test_db(schema_sql: str = None) -> Generator[TestDatabase, None, None]:
    """
    Context manager for SQLite test database.
    
    Usage:
        with sqlite_test_db() as db:
            db.execute("CREATE TABLE test (id INTEGER)")
            results = db.query("SELECT * FROM test")
    """
    db = TestDatabase(db_type="sqlite")
    db.create_sqlite_db()
    
    if schema_sql:
        # Execute each statement separately
        for statement in schema_sql.split(';'):
            statement = statement.strip()
            if statement:
                db.execute(statement)
    
    try:
        yield db
    finally:
        db.close()


@contextmanager
def postgres_test_db(config: DatabaseConfig = None) -> Generator[TestDatabase, None, None]:
    """
    Context manager for PostgreSQL test database.
    
    Usage:
        with postgres_test_db() as db:
            db.execute("CREATE TABLE test (id SERIAL)")
            results = db.query("SELECT * FROM test")
    """
    db = TestDatabase(db_type="postgres")
    
    if not db.create_postgres_db(config):
        raise RuntimeError("PostgreSQL not available")
    
    try:
        yield db
    finally:
        db.close()


# JWT Token Fixtures
def create_test_token(
    username: str = "testuser",
    roles: list = None,
    expires_in: int = 3600
) -> dict:
    """
    Create test JWT token data.
    
    Returns:
        Dictionary with access_token, refresh_token, token_type
    """
    import time
    import base64
    import json
    
    roles = roles or ["user"]
    
    # Create header
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64.b64encode(
        json.dumps(header).encode()
    ).decode().rstrip("=")
    
    # Create payload
    now = int(time.time())
    payload = {
        "sub": username,
        "roles": roles,
        "iat": now,
        "exp": now + expires_in
    }
    payload_b64 = base64.b64encode(
        json.dumps(payload).encode()
    ).decode().rstrip("=")
    
    # Create signature (dummy for testing)
    signature = "dummysignature"
    
    access_token = f"{header_b64}.{payload_b64}.{signature}"
    
    return {
        "access_token": access_token,
        "refresh_token": f"refresh_{username}_{int(time.time())}",
        "token_type": "bearer"
    }


def create_expired_token(username: str = "testuser") -> dict:
    """Create expired test token."""
    return create_test_token(username, expires_in=-3600)


# Common test schemas
SQLITE_TEST_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT,
    roles TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    content TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    data TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

POSTGRES_TEST_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255),
    roles JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(255) PRIMARY KEY,
    content TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events (
    id VARCHAR(255) PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    data JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


if __name__ == "__main__":
    # Test fixtures
    print("Testing shared fixtures...")
    
    # Test SQLite fixture
    with sqlite_test_db(SQLITE_TEST_SCHEMA) as db:
        db.execute("INSERT INTO users (username, email) VALUES (?, ?)", ("test", "test@test.com"))
        results = db.query("SELECT * FROM users")
        print(f"SQLite test: {len(results)} rows")
    
    # Test JWT fixture
    token = create_test_token("testuser", ["admin", "user"])
    print(f"JWT test: access_token present = {bool(token['access_token'])}")
    
    print("Fixtures test complete")

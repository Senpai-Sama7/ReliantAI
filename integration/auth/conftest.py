"""Shared pytest configuration for auth service tests."""

import os


os.environ.setdefault(
    "AUTH_SECRET_KEY",
    "test-auth-secret-key-0123456789abcdefghijklmnopqrstuvwxyz",
)

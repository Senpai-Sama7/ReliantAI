#!/usr/bin/env python3
"""Setup script for reliant-shared package."""

from setuptools import setup, find_packages

setup(
    name="reliant-shared",
    version="1.0.0",
    description="Shared utilities for ReliantAI integration",
    author="ReliantAI Team",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.109.0",
        "python-jose[cryptography]>=3.3.0",
        "requests>=2.32.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
        ]
    },
    python_requires=">=3.11",
)

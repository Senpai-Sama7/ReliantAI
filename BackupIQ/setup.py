#!/usr/bin/env python3
"""
Setup script for Intelligent Backup Enterprise System
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements
def read_requirements(filename):
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name="intelligent-backup-enterprise",
    version="1.0.0",
    description="Enterprise-grade backup system with semantic file organization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Enterprise Development Team",
    author_email="dev-team@company.com",
    url="https://github.com/company/intelligent-backup-enterprise",

    # Package discovery
    packages=find_packages(where="src"),
    package_dir={"": "src"},

    # Dependencies
    install_requires=read_requirements("requirements.txt"),
    extras_require={
        "dev": read_requirements("requirements-dev.txt"),
        "all": read_requirements("requirements.txt") + read_requirements("requirements-dev.txt"),
    },

    # Python version requirement
    python_requires=">=3.9",

    # Entry points
    entry_points={
        "console_scripts": [
            "backup-enterprise=core.backup_orchestrator:main",
            "backup-config=core.config_manager:main",
            "backup-test=tests.test_runner:main",
        ],
    },

    # Package data
    include_package_data=True,
    package_data={
        "": [
            "config/*.yml",
            "config/*.yaml",
            "config/*.json",
            "scripts/*.sh",
            "monitoring/*.yml",
            "deployment/*.yaml",
        ]
    },

    # Classifiers
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Archiving :: Backup",
        "Topic :: System :: Systems Administration",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],

    # Keywords
    keywords="backup enterprise cloud storage semantic organization",

    # Project URLs
    project_urls={
        "Documentation": "https://docs.company.com/intelligent-backup",
        "Source": "https://github.com/company/intelligent-backup-enterprise",
        "Tracker": "https://github.com/company/intelligent-backup-enterprise/issues",
    },
)
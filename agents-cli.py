#!/usr/bin/env python3
"""Direct entry point for agents-cli. Run from project root."""
import sys
import os

# Ensure project root is on path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from reliantai.agents.cli import cli

if __name__ == "__main__":
    cli()

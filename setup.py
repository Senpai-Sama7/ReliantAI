#!/usr/bin/env python3
"""
Placeholder setup.py — interactive setup moved to scripts/setup_wizard.py

This file used to contain the setup wizard CLI. It has been moved to scripts/setup_wizard.py
to avoid conflicts with Python packaging conventions.
"""
import sys

if __name__ == "__main__":
    print("ReliantAI setup wizard has moved.")
    print("Run: python3 scripts/setup_wizard.py")
    print("\nFor more info, see scripts/legacy_setup_cli.py (the previous version)")
    sys.exit(0)
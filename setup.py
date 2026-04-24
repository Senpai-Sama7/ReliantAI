#!/usr/bin/env python3
"""
Placeholder setup.py - Interactive setup moved to scripts/setup_wizard.py

This file was previously the interactive setup wizard. It has been moved to
scripts/setup_wizard.py to avoid conflicts with Python packaging conventions.

For initial setup, run:
    python3 scripts/setup_wizard.py

For more information:
    python3 scripts/setup_wizard.py --help
"""
import sys

if __name__ == "__main__":
    print("ReliantAI setup wizard has moved.")
    print("Run: python3 scripts/setup_wizard.py")
    print("\nFor non-interactive setup (CI/automation):")
    print("  python3 scripts/setup_wizard.py -y")
    print("\nFor help:")
    print("  python3 scripts/setup_wizard.py --help")
    sys.exit(0)

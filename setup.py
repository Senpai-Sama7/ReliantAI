#!/usr/bin/env python3
"""
Compatibility wrapper for setup.py - forwards to scripts/setup_wizard.py

This file was previously the interactive setup wizard. It has been moved to
scripts/setup_wizard.py to avoid conflicts with Python packaging conventions.

This wrapper preserves backward compatibility for deployment scripts and other
tools that may call setup.py directly.
"""
import sys
import os
import subprocess

if __name__ == "__main__":
    # Get the directory of this file
    project_root = os.path.dirname(os.path.abspath(__file__))
    setup_wizard = os.path.join(project_root, "scripts", "setup_wizard.py")

    # Check if setup_wizard exists and is executable
    if os.path.exists(setup_wizard):
        # Forward all arguments to the setup wizard
        try:
            result = subprocess.run(
                [sys.executable, setup_wizard] + sys.argv[1:],
                cwd=project_root
            )
            sys.exit(result.returncode)
        except Exception as e:
            print(f"Error running setup wizard: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Fallback message if setup_wizard doesn't exist
        print("ReliantAI setup wizard has moved.")
        print("Run: python3 scripts/setup_wizard.py")
        print("\nFor non-interactive setup (CI/automation):")
        print("  python3 scripts/setup_wizard.py -y")
        print("\nFor help:")
        print("  python3 scripts/setup_wizard.py --help")
        sys.exit(1)

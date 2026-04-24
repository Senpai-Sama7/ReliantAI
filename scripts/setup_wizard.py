#!/usr/bin/env python3
"""
ReliantAI Initial Setup Wizard

A friendly CLI tool to configure the environment for first-time users.

Improvements made:
- Avoid non-portable special characters that cause encoding issues
- Use getpass for secret inputs (no terminal echo)
- Create timestamped backups before overwriting .env
- Portable empty file creation (works on Windows and Unix)
- Regex-based env variable replacement (handles comments and spaces)
- Unattended mode (--yes/-y flag) for automation and CI
- UTF-8 encoding enforcement, proper error handling
"""
import os
import sys
import shutil
import re
import argparse
import datetime
import getpass
from typing import Optional, Match, Callable

# ANSI Colors (gracefully degrade if terminal doesn't support)
C_BLUE = "\033[94m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_MAGENTA = "\033[95m"
C_RESET = "\033[0m"

def supports_color():
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

def color(text, code):
    if supports_color():
        return f"{code}{text}{C_RESET}"
    return text

def print_header():
    print()
    print(color("==============================================", C_BLUE))
    print(color("  Welcome to ReliantAI Platform - Setup Wizard", C_BLUE))
    print(color("==============================================", C_BLUE))
    print("It looks like this is your first time running the platform.")
    print("Let's get your environment configured quickly.\n")

def ask(
    prompt_text: str,
    default: Optional[str] = None,
    is_secret: bool = False,
    unattended_default: Optional[str] = None,
) -> str:
    """Prompt user for input.

    Args:
        prompt_text: Prompt to display
        default: Default value if user presses Enter
        is_secret: Use getpass to hide input
        unattended_default: Value to use in unattended mode

    Returns:
        User input or default value
    """
    if is_secret:
        prompt = f"{prompt_text}{' [hidden]' if default is None else ' [hidden, Enter=use existing]'}: "
        if unattended_default is not None:
            val = unattended_default
        else:
            try:
                val = getpass.getpass(prompt)
            except EOFError:
                val = ""
    else:
        if default:
            prompt = f"{prompt_text} [{color(default, C_GREEN)}]: "
        else:
            prompt = f"{prompt_text}: "
        if unattended_default is not None:
            val = unattended_default
        else:
            try:
                val = input(prompt)
            except EOFError:
                val = ""

    val = (val or "").strip()
    if not val and default is not None:
        return default
    return val

ENV_KEYS_TO_PROMPT = [
    ("GEMINI_API_KEY", "Google Gemini API Key (CrewAI Triage)", True),
    ("GOOGLE_PLACES_API_KEY", "Google Places API Key (Lead Generation)", True),
    ("TWILIO_SID", "Twilio Account SID (SMS Outreach)", False),
    ("TWILIO_TOKEN", "Twilio Auth Token", True),
    ("STRIPE_SECRET_KEY", "Stripe Secret Key (Billing)", True),
]

def read_file(path: str) -> Optional[str]:
    """Read file with UTF-8 encoding."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None

def write_file(path: str, content: str) -> None:
    """Write file with UTF-8 encoding."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def set_env_var(content: str, key: str, value: str) -> str:
    """Set or replace an environment variable in .env content.

    Uses regex to find and replace existing key=value pairs, preserving
    any trailing comments. Appends if the key doesn't exist.

    Args:
        content: Current .env file content
        key: Environment variable name
        value: New value to set

    Returns:
        Updated content
    """
    if value is None or value == "":
        return content

    # Pattern to match KEY=value, preserving trailing comments and indentation
    # Captures: key= prefix, value+spaces, and optional comment
    pattern = re.compile(
        rf"(^\s*{re.escape(key)}\s*=)([^#\n\r]*)(\s*#.*)?$",
        re.MULTILINE
    )

    def replacer(match: Match[str]) -> str:
        prefix = match.group(1)  # KEY=
        value_with_space = match.group(2).rstrip()  # value (strip trailing space)
        comment = match.group(3) or ""  # trailing comment (with leading space if present)
        # Reconstruct with space before comment if comment exists
        if comment:
            return f"{prefix}{value} {comment.lstrip()}"
        return f"{prefix}{value}"

    if pattern.search(content):
        # Replace only the value part, preserving structure and comments
        content = pattern.sub(replacer, content)
    else:
        # Append new key=value pair
        new_line = f"{key}={value}"
        if not content.endswith("\n") and content != "":
            content += "\n"
        content += new_line + "\n"

    return content

def backup_file(path: str) -> Optional[str]:
    """Create a timestamped backup of a file."""
    if not os.path.exists(path):
        return None

    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bak = f"{path}.bak.{ts}"
    shutil.copy2(path, bak)
    return bak

def create_empty_file(path: str) -> None:
    """Safely create an empty file (portable for Windows and Unix)."""
    open(path, "w", encoding="utf-8").close()

def run_setup(unattended: bool = False) -> None:
    """Run the setup wizard."""
    print_header()

    # Go up two levels: scripts/setup_wizard.py → scripts → ReliantAI (project root)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_file = os.path.join(project_root, ".env")
    env_example = os.path.join(project_root, ".env.example")

    # If .env exists, back it up before changing
    if os.path.exists(env_file):
        print(color("Existing .env detected. Creating a backup...", C_YELLOW))
        bak = backup_file(env_file)
        if bak:
            print(color(f"Backup created at: {bak}", C_GREEN))

        if not unattended:
            try:
                resp = input("Do you want to overwrite it? (y/N): ").strip().lower()
            except EOFError:
                resp = "n"
            if resp != "y":
                print("Setup cancelled.")
                sys.exit(0)

    # If example exists, copy it to .env; otherwise create an empty .env
    if os.path.exists(env_example):
        shutil.copy2(env_example, env_file)
    else:
        print(color("Warning: .env.example not found. Creating a blank .env.", C_YELLOW))
        create_empty_file(env_file)

    print(f"\n{color('-- Core API Integrations (Optional but recommended) --', C_MAGENTA)}")
    print("These are required for the AI Engine, Lead Generation, and SMS outreach.")
    print("Press Enter to skip if you just want to run local development mode.\n")

    # Read current env content
    content = read_file(env_file)
    if content is None:
        content = ""

    # Extract current defaults from file (handles quoted strings with # correctly)
    current_values = {}
    for key, prompt_text, is_secret in ENV_KEYS_TO_PROMPT:
        # Regex handles: unquoted values, single-quoted with escapes, double-quoted with escapes
        m = re.search(
            rf"^\s*{re.escape(key)}\s*=\s*('(?:[^']|\\')*'|\"(?:[^\"]|\\\")*\"|[^#\n\r]*)",
            content,
            re.MULTILINE
        )
        if m and m.group(1):
            val = m.group(1).strip()
            # Remove quotes if present, but keep content intact
            if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                val = val[1:-1]
            current_values[key] = val
        else:
            current_values[key] = ""

    # Prompt user for each key
    for key, prompt_text, is_secret in ENV_KEYS_TO_PROMPT:
        default = current_values.get(key) or None
        unattended_default = None
        if unattended:
            unattended_default = default or ""

        val = ask(prompt_text, default=default, is_secret=is_secret, unattended_default=unattended_default)
        if val:
            content = set_env_var(content, key, val)

    # Write updated content
    write_file(env_file, content)

    print(color("\n✓ Configuration saved to .env!", C_GREEN))
    print(f"You can edit {color('.env', C_GREEN)} directly at any time to add more secrets.\n")
    print("For more information, see: scripts/setup_wizard.py --help")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="ReliantAI initial setup wizard",
        epilog="Example: python3 scripts/setup_wizard.py -y"
    )
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Run non-interactively and accept defaults/backup overwrites (useful for CI)"
    )
    args = parser.parse_args()

    try:
        run_setup(unattended=args.yes)
    except KeyboardInterrupt:
        print(f"\n{color('Setup cancelled.', C_YELLOW)}")
        sys.exit(1)

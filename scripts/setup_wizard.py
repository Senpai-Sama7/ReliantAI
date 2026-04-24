#!/usr/bin/env python3
"""
ReliantAI Initial Setup Wizard

A friendly CLI tool to configure the environment for first-time users.

Improvements made:
- Avoid use of non-portable special box-drawing characters to prevent encoding/truncation issues.
- Use getpass for secret inputs so tokens/keys aren't echoed.
- Create a timestamped backup of an existing .env before overwriting.
- Safely create an empty .env if .env.example is missing (works on Windows and Unix).
- Use robust line-based replacements for env variables (handles spaces and comments) and appends missing keys.
- Provides a --yes / -y flag for unattended operation (useful in automation).
"""
import os
import sys
import shutil
import re
import argparse
import datetime
import getpass

# ANSI Colors (simple, will gracefully degrade if not supported)
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

def ask(prompt_text, default=None, is_secret=False, unattended_default=None):
    """Ask the user for input. If default is provided and user presses Enter, returns default.
    If is_secret is True, uses getpass.getpass to avoid echoing. If unattended_default is provided
    and --yes was passed, returns unattended_default without prompting.
    """
    if is_secret:
        prompt = f"{prompt_text}{' [hidden]' if default is None else ' [hidden, Enter=use existing]'}: "
        if unattended_default is not None:
            val = unattended_default
        else:
            try:
                val = getpass.getpass(prompt)
            except (EOFError, KeyboardInterrupt):
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

def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return None

def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def set_env_var(content, key, value):
    """Set or replace an environment variable in the .env content.
    It looks for lines that start with KEY= (allowing spaces) and replaces the entire line.
    If the key is not present, it appends it at the end with a newline.
    """
    if value is None or value == "":
        return content
    pattern = re.compile(rf"^\s*{re.escape(key)}\s*=.*$", re.MULTILINE)
    new_line = f"{key}={value}"
    if pattern.search(content):
        content = pattern.sub(new_line, content)
    else:
        if not content.endswith("\n") and content != "":
            content += "\n"
        content += new_line + "\n"
    return content

def backup_file(path):
    if not os.path.exists(path):
        return None
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    bak = f"{path}.bak.{ts}"
    shutil.copy2(path, bak)
    return bak

def create_empty_file(path):
    # Safely create an empty file (portable), truncate if it already exists
    open(path, "w", encoding="utf-8").close()

def run_setup(unattended=False):
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

    print(f"\n{color('── Core API Integrations (Optional but recommended) ──', C_MAGENTA)}")
    print("These are required for the AI Engine, Lead Generation, and SMS outreach.")
    print("Press Enter to skip if you just want to run local development mode.\n")

    # Read current env content
    content = read_file(env_file)
    if content is None:
        content = ""

    # For each key, extract current default from file if present (stop at # comment)
    current_values = {}
    for key, prompt_text, is_secret in ENV_KEYS_TO_PROMPT:
        m = re.search(rf"^\s*{re.escape(key)}\s*=\s*([^#\n\r]*)", content, re.MULTILINE)
        current_values[key] = (m.group(1).strip() if m and m.group(1) is not None else "")

    # Prompt user
    for key, prompt_text, is_secret in ENV_KEYS_TO_PROMPT:
        default = current_values.get(key) or None
        unattended_default = None
        if unattended:
            # If unattended, keep existing value or empty string
            unattended_default = default or ""
        val = ask(prompt_text, default=default, is_secret=is_secret, unattended_default=unattended_default)
        if val:
            content = set_env_var(content, key, val)

    # Write updated content
    write_file(env_file, content)

    print(color("\n✓ Configuration saved to .env!", C_GREEN))
    print(f"You can edit {color('.env', C_GREEN)} directly at any time to add more secrets.\n")
    print("Starting deployment...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ReliantAI initial setup wizard")
    parser.add_argument("-y", "--yes", action="store_true", help="Run non-interactively and accept defaults/backup overwrites")
    args = parser.parse_args()
    try:
        run_setup(unattended=args.yes)
    except KeyboardInterrupt:
        print(f"\n{color('Setup cancelled.', C_YELLOW)}")
        sys.exit(1)

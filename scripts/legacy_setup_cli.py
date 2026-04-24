#!/usr/bin/env python3
"""
ReliantAI Initial Setup Wizard (Legacy)

A friendly CLI tool to configure the environment for first-time users.
This is the original version preserved for backward compatibility.
"""

import os
import sys
import shutil

# ANSI Colors
C_BLUE = "\033[94m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_MAGENTA = "\033[95m"
C_RESET = "\033[0m"

def print_header():
    print(f"\n{C_BLUE}═══════════════════════════════════════════════════════════════{C_RESET}")
    print(f"{C_BLUE}  🚀 Welcome to ReliantAI Platform{C_RESET}")
    print(f"{C_BLUE}═══════════════════════════════════════════════════════════════{C_RESET}\n")
    print("It looks like this is your first time running the platform.")
    print("Let's get your environment configured quickly.\n")

def ask(prompt_text, default="", is_secret=False):
    if default:
        prompt = f"{prompt_text} [{C_GREEN}{default}{C_RESET}]: "
    else:
        prompt = f"{prompt_text}: "

    val = input(prompt).strip()
    return val if val else default

def run_setup():
    print_header()

    # Go up two levels: scripts/legacy_setup_cli.py → scripts → ReliantAI (project root)
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env_file = os.path.join(project_root, ".env")
    env_example = os.path.join(project_root, ".env.example")

    if os.path.exists(env_file):
        print(f"{C_YELLOW}An .env file already exists!{C_RESET}")
        resp = input("Do you want to overwrite it? (y/N): ").lower()
        if resp != 'y':
            print("Setup cancelled.")
            sys.exit(0)

    if not os.path.exists(env_example):
        print(f"{C_YELLOW}Warning: .env.example not found. Creating a blank .env.{C_RESET}")
        shutil.copy("/dev/null", env_file)
    else:
        shutil.copy(env_example, env_file)

    print(f"\n{C_MAGENTA}── Core API Integrations (Optional but recommended) ──{C_RESET}")
    print("These are required for the AI Engine, Lead Generation, and SMS outreach.")
    print("Press Enter to skip if you just want to run local development mode.\n")

    gemini_key = ask("Google Gemini API Key (CrewAI Triage)")
    places_key = ask("Google Places API Key (Lead Generation)")
    twilio_sid = ask("Twilio Account SID (SMS Outreach)")
    twilio_tok = ask("Twilio Auth Token")
    stripe_key = ask("Stripe Secret Key (Billing)")

    # Read the copied .env and replace the lines
    with open(env_file, 'r') as f:
        content = f.read()

    # Apply the user's inputs
    if gemini_key:
        content = content.replace("GEMINI_API_KEY=             # Required for CrewAI triage", f"GEMINI_API_KEY={gemini_key}")
    if places_key:
        # If GOOGLE_PLACES_API_KEY isn't in there, append it
        if "GOOGLE_PLACES_API_KEY" in content:
            content = content.replace("GOOGLE_PLACES_API_KEY=", f"GOOGLE_PLACES_API_KEY={places_key}")
        else:
            content += f"\nGOOGLE_PLACES_API_KEY={places_key}\n"

    if twilio_sid:
        content = content.replace("TWILIO_SID=                 # Required for SMS integration", f"TWILIO_SID={twilio_sid}")
    if twilio_tok:
        content = content.replace("TWILIO_TOKEN=               # Required for SMS integration", f"TWILIO_TOKEN={twilio_tok}")
    if stripe_key:
        if "STRIPE_SECRET_KEY" in content:
            content = content.replace("STRIPE_SECRET_KEY=", f"STRIPE_SECRET_KEY={stripe_key}")
        else:
            content += f"\nSTRIPE_SECRET_KEY={stripe_key}\n"

    with open(env_file, 'w') as f:
        f.write(content)

    print(f"\n{C_GREEN}✓ Configuration saved to .env!{C_RESET}")
    print(f"You can edit {C_GREEN}.env{C_RESET} directly at any time to add more secrets.\n")
    print("Starting deployment...")

if __name__ == "__main__":
    try:
        run_setup()
    except KeyboardInterrupt:
        print(f"\n{C_YELLOW}Setup cancelled.{C_RESET}")
        sys.exit(1)

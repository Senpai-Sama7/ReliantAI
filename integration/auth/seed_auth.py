#!/usr/bin/env python3
"""
Seed script for ReliantAI Auth Service.
Creates bootstrap users directly in SQLite (bypasses role-escalation blocks).
Run AFTER auth_server.py is running.

Usage:
    python3 seed_auth.py [--admin-password PASSWORD] [--service-password PASSWORD]
"""

import argparse
import sys
import sqlite3
from pathlib import Path
import bcrypt

AUTH_DB_PATH = Path(__file__).parent / "auth.db"


def hash_password(password: str) -> str:
    truncated = password.encode("utf-8")[:72]
    hashed = bcrypt.hashpw(truncated, bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")


def seed_users(admin_password: str, service_password: str) -> None:
    if not AUTH_DB_PATH.exists():
        print(f"ERROR: Auth DB not found at {AUTH_DB_PATH}")
        print("Start auth_server.py first, then run this script.")
        sys.exit(1)

    conn = sqlite3.connect(AUTH_DB_PATH)
    cursor = conn.cursor()

    from datetime import datetime, UTC

    users = [
        {
            "username": "admin",
            "email": "admin@reliantai.local",
            "hashed_password": hash_password(admin_password),
            "role": "admin",
            "tenant_id": "system",
        },
        {
            "username": "service",
            "email": "service@reliantai.local",
            "hashed_password": hash_password(service_password),
            "role": "operator",
            "tenant_id": "system",
        },
    ]

    now = datetime.utcnow().isoformat()

    for user in users:
        # Check if user exists
        cursor.execute(
            "SELECT username FROM users WHERE username = ?", (user["username"],)
        )
        existing = cursor.fetchone()

        if existing:
            # Update existing user
            cursor.execute(
                """
                UPDATE users SET email=?, hashed_password=?, role=?, tenant_id=?, updated_at=?
                WHERE username=?
                """,
                (
                    user["email"],
                    user["hashed_password"],
                    user["role"],
                    user["tenant_id"],
                    now,
                    user["username"],
                ),
            )
            print(f"Updated user: {user['username']} (role={user['role']})")
        else:
            # Insert new user
            cursor.execute(
                """
                INSERT INTO users (username, email, hashed_password, role, tenant_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user["username"],
                    user["email"],
                    user["hashed_password"],
                    user["role"],
                    user["tenant_id"],
                    now,
                    now,
                ),
            )
            print(f"Created user: {user['username']} (role={user['role']})")

    conn.commit()
    conn.close()
    print("Bootstrap users seeded successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Seed ReliantAI Auth Service bootstrap users"
    )
    parser.add_argument(
        "--admin-password",
        default="SecureAdminPass123!",
        help="Password for admin user",
    )
    parser.add_argument(
        "--service-password",
        default="ServicePass123!",
        help="Password for service user",
    )
    args = parser.parse_args()

    print(f"Seeding bootstrap users into {AUTH_DB_PATH}...")
    seed_users(args.admin_password, args.service_password)

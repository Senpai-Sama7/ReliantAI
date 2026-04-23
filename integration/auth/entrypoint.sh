#!/bin/sh
set -e

python -c "import asyncio; from user_store import SQLiteUserStore; asyncio.run(SQLiteUserStore('/app/auth.db').initialize())" || true
exec python auth_server.py

#!/bin/bash
# bootstrap_env.sh — Generate .env files from .env.example templates
set -euo pipefail

PROJECTS=("integration" "B-A-P" "Money" "Citadel" "ClearDesk" "Gen-H" "intelligent-storage" "Acropolis" "apex")

for project in "${PROJECTS[@]}"; do
    example="$project/.env.example"
    target="$project/.env"
    if [ -f "$example" ] && [ ! -f "$target" ]; then
        cp "$example" "$target"
        echo "✅ Created $target from $example"
    elif [ -f "$target" ]; then
        echo "⏭️  $target already exists, skipping"
    else
        echo "⚠️  No .env.example found for $project"
    fi
done

# Generate secrets for auth
AUTH_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(64))")
if [ -f "integration/.env" ]; then
    # Ensure it's not already there
    if ! grep -q "AUTH_SECRET_KEY=" integration/.env; then
        echo "AUTH_SECRET_KEY=$AUTH_SECRET" >> integration/.env
        echo "🔑 Generated AUTH_SECRET_KEY for integration"
    fi
fi

echo ""
echo "Done. Review and update each .env file with real values."

#!/bin/bash
# Intelligent Storage Nexus - Dependency Installation Script
# Automates setup of PostgreSQL extensions and Python environment.

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting Intelligent Storage Nexus dependency setup...${NC}"

# 1. Update system packages
echo -e "${BLUE}🔄 Updating package lists...${NC}"
sudo apt-get update -y

# 2. Install Python 3 and essential build tools
echo -e "${BLUE}🐍 Installing Python 3 and build essentials...${NC}"
sudo apt-get install -y python3 python3-pip python3-venv build-essential libpq-dev

# 3. PostgreSQL Installation & Extensions
echo -e "${BLUE}🐘 Setting up PostgreSQL and Extensions...${NC}"

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}⚠️  PostgreSQL not found. Installing PostgreSQL 17...${NC}"
    # Add PostgreSQL official repo for Ubuntu
    sudo apt-get install -y curl ca-certificates
    sudo install -d /usr/share/postgresql-common/pgdg
    sudo curl -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc --fail https://www.postgresql.org/media/keys/ACCC4CF8.asc
    sudo sh -c 'echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
    sudo apt-get update -y
    sudo apt-get install -y postgresql-17
fi

# Determine PostgreSQL version to install the correct extension package
PG_VERSION=$(psql --version | grep -oE '[0-9]+' | head -1)
echo -e "${BLUE}ℹ️  Detected PostgreSQL version: ${PG_VERSION}${NC}"

# Install pgvector and contrib (for pg_trgm)
echo -e "${BLUE}📦 Installing pgvector and contrib extensions...${NC}"
sudo apt-get install -y "postgresql-${PG_VERSION}-pgvector" "postgresql-contrib"

# Optional: Apache AGE (Pointer only as it often requires source build)
echo -e "${YELLOW}ℹ️  Note: Apache AGE is preferred for advanced graph features.${NC}"
echo -e "${YELLOW}   If you need Cypher support, visit: https://age.apache.org/set_up/age_installation_guide/${NC}"

# 4. Python Virtual Environment Setup
echo -e "${BLUE}🛠️  Setting up Python virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created.${NC}"
else
    echo -e "${YELLOW}ℹ️  Virtual environment already exists.${NC}"
fi

# 5. Install Python Dependencies
echo -e "${BLUE}📥 Installing Python dependencies from requirements.txt...${NC}"
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 6. Database Verification
echo -e "${BLUE}🔍 Verifying PostgreSQL extensions...${NC}"
echo -e "${YELLOW}Please ensure your PostgreSQL server is running.${NC}"

# Attempt to enable extensions in the default database template (requires superuser)
# This is a best-effort step.
echo -e "${BLUE}ℹ️  Attempting to enable extensions in template1 (requires superuser)...${NC}"
sudo -u postgres psql -d template1 -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;" || echo -e "${YELLOW}   Note: Could not enable pg_trgm in template1 via sudo. Please enable manually if needed.${NC}"
sudo -u postgres psql -d template1 -c "CREATE EXTENSION IF NOT EXISTS vector;" || echo -e "${YELLOW}   Note: Could not enable pgvector in template1 via sudo. Please enable manually if needed.${NC}"

echo -e ""
echo -e "${GREEN}✅ Setup Complete!${NC}"
echo -e "${BLUE}Next Steps:${NC}"
echo -e "1. Configure your environment in ${YELLOW}config.py${NC} or ${YELLOW}.env${NC}"
echo -e "2. Initialize your database: ${YELLOW}source venv/bin/activate && psql -h localhost -U storage_admin -d intelligent_storage -f schema.sql${NC}"
echo -e "3. Start the system: ${YELLOW}./start.sh${NC}"
echo -e ""

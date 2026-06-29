#!/bin/bash
cd /home/donovan/Projects/platforms/ReliantAI
export PYTHONPATH=/home/donovan/Projects/platforms/ReliantAI
export DATABASE_URL=postgresql://reliantai:reliantai_dev@localhost:5433/reliantai
export REDIS_URL=redis://localhost:6379/0
export API_SECRET_KEY=dev_secret_key_change_in_production
export REVALIDATE_SECRET=c0568b2286d42bca3cac59ece4e719c6b5a434cac83745a825909f9200dec0e1
exec python3 -m uvicorn --host 0.0.0.0 --port 8000 reliantai.main:app

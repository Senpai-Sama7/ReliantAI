"""
Script to ingest data into the Vector Search Service.

This script allows users to easily add text documents to the vector search
index. It reads a JSON file containing documents and sends them to the
`/vector/index` endpoint of the API Gateway.

Usage:
    python scripts/ingest_vector_data.py <path_to_json_file>

JSON file format:
[
    {"id": "doc1", "text": "The quick brown fox jumps over the lazy dog."},
    {"id": "doc2", "text": "Artificial intelligence is rapidly advancing."}
]
"""

import sys
import json
import httpx
import asyncio

VECTOR_INDEX_URL = "http://localhost:8000/vector/index"

async def ingest_data(file_path: str):
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        sys.exit(1)

    with open(file_path, "r") as f:
        documents = json.load(f)

    if not isinstance(documents, list):
        print("Error: JSON file must contain a list of documents.")
        sys.exit(1)

    print(f"Attempting to ingest {len(documents)} documents...")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(VECTOR_INDEX_URL, json=documents, timeout=300.0) # Increased timeout for large files
            response.raise_for_status()
            result = response.json()
            print(f"Successfully ingested data: {result}")
        except httpx.RequestError as e:
            print(f"Network error during ingestion: {e}")
            sys.exit(1)
        except httpx.HTTPStatusError as e:
            print(f"HTTP error during ingestion: {e.response.status_code} - {e.response.text}")
            sys.exit(1)
        except Exception as e:
            print(f"An unexpected error occurred during ingestion: {e}")
            sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/ingest_vector_data.py <path_to_json_file>")
        sys.exit(1)
    
    import os
    asyncio.run(ingest_data(sys.argv[1]))

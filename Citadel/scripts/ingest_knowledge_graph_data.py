"""
Script to ingest data into the Knowledge Graph Service.

This script allows users to easily add nodes and relationships to the knowledge
graph. It reads a JSON file containing Cypher queries and sends them to the
`/knowledge/query` endpoint of the API Gateway.

Usage:
    python scripts/ingest_knowledge_graph_data.py <path_to_json_file>

JSON file format (list of Cypher queries):
[
    "CREATE (p:Person {name: 'Alice'})",
    "CREATE (c:City {name: 'New York'})",
    "MATCH (p:Person {name: 'Alice'}), (c:City {name: 'New York'}) CREATE (p)-[:LIVES_IN]->(c)"
]
"""

import sys
import json
import httpx
import asyncio

KNOWLEDGE_GRAPH_URL = "http://localhost:8000/knowledge/query"

async def ingest_data(file_path: str):
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        sys.exit(1)

    with open(file_path, "r") as f:
        queries = json.load(f)

    if not isinstance(queries, list) or not all(isinstance(q, str) for q in queries):
        print("Error: JSON file must contain a list of Cypher query strings.")
        sys.exit(1)

    print(f"Attempting to execute {len(queries)} Cypher queries...")

    async with httpx.AsyncClient() as client:
        for i, query in enumerate(queries):
            print(f"Executing query {i+1}/{len(queries)}: {query[:70]}...")
            try:
                response = await client.post(KNOWLEDGE_GRAPH_URL, json={"query": query}, timeout=60.0)
                response.raise_for_status()
                result = response.json()
                print(f"  Success: {result}")
            except httpx.RequestError as e:
                print(f"  Network error during query: {e}")
                sys.exit(1)
            except httpx.HTTPStatusError as e:
                print(f"  HTTP error during query: {e.response.status_code} - {e.response.text}")
                sys.exit(1)
            except Exception as e:
                print(f"  An unexpected error occurred during query: {e}")
                sys.exit(1)
    print("All queries executed.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/ingest_knowledge_graph_data.py <path_to_json_file>")
        sys.exit(1)
    
    import os
    asyncio.run(ingest_data(sys.argv[1]))

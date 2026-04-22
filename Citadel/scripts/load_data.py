"""
Helper script to load sample data into the services via HTTP.

Run this script after starting the stack to populate the vector search
index, the knowledge graph and the hierarchical classification model
with their respective sample datasets. This is optional but makes the
demo more interesting when exploring the APIs.
"""

import json
import os
from pathlib import Path

import httpx


BASE_URL = os.environ.get("GATEWAY_URL", "http://localhost:8000")


async def load_vector_data():
    path = Path(__file__).resolve().parents[1] / "services/vector_search/sample_data/docs.json"
    docs = json.loads(path.read_text())
    async with httpx.AsyncClient() as client:
        await client.post(f"{BASE_URL}/vector/index", json=docs)


async def load_graph_data():
    path = Path(__file__).resolve().parents[1] / "services/knowledge_graph/sample_data/init.cypher"
    cypher = path.read_text()
    async with httpx.AsyncClient() as client:
        # Note: the graph service does not yet expose a bulk load endpoint, so we run queries line by line
        for line in cypher.split(";\n"):
            line = line.strip()
            if not line:
                continue
            await client.post(f"{BASE_URL}/knowledge/query", json={"cypher": line})


async def load_hierarchical_data():
    import pandas as pd

    train_path = Path(__file__).resolve().parents[1] / "services/hierarchical_classification/sample_data/train.csv"
    df = pd.read_csv(train_path)
    features = df[[c for c in df.columns if c.startswith("x")]].to_dict(orient="records")
    labels = df[[c for c in df.columns if not c.startswith("x")]].to_dict(orient="records")
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/hier/train", json={"features": features, "labels": labels}
        )
        model_id = resp.json().get("model_id")
        print(f"Trained hierarchical classifier with id {model_id}")


async def main():
    await load_vector_data()
    await load_graph_data()
    await load_hierarchical_data()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
#!/usr/bin/env python3
"""Benchmark embedding models for speed and quality comparison.

Usage:
    python3 benchmark_embeddings.py [--models MODEL1,MODEL2] [--samples N]
"""

import asyncio
import json
import sys
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

import asyncpg
import httpx
from datetime import datetime

from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS, OLLAMA_URL


@dataclass
class BenchmarkResult:
    """Results for a single model benchmark."""

    model: str
    dimensions: int
    avg_embed_time_ms: float
    throughput_per_sec: float
    memory_mb: float
    search_quality_score: float
    notes: str = ""


# Model specifications (dimensions, etc.)
MODEL_SPECS = {
    "nomic-embed-text:latest": {
        "dimensions": 768,
        "supports_matryoshka": False,
        "description": "Current production model - 137M params",
    },
    "mxbai-embed-large:latest": {
        "dimensions": 1024,
        "supports_matryoshka": False,
        "description": "Mixedbread AI - 335M params",
    },
    "snowflake-arctic-embed2": {
        "dimensions": 768,
        "supports_matryoshka": True,
        "matryoshka_dims": [256, 512, 768],
        "description": "Snowflake - supports MRL (Matryoshka)",
    },
}


async def get_sample_files(conn: asyncpg.Connection, limit: int = 100) -> List[Dict]:
    """Fetch random sample files from database with content previews."""
    rows = await conn.fetch(
        """
        SELECT f.id, f.name, f.extension, f.content_preview
        FROM files f
        JOIN file_embeddings fe ON f.id = fe.file_id
        WHERE f.content_preview IS NOT NULL
          AND LENGTH(f.content_preview) > 50
        ORDER BY RANDOM()
        LIMIT $1
        """,
        limit,
    )
    return [dict(row) for row in rows]


async def benchmark_embedding_speed(
    client: httpx.AsyncClient, model: str, texts: List[str], batch_size: int = 32
) -> tuple[float, float]:
    """Benchmark embedding generation speed.

    Returns:
        (avg_time_ms, throughput_per_sec)
    """
    times = []

    # Process in batches
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]

        start = time.perf_counter()
        resp = await client.post(
            OLLAMA_URL, json={"model": model, "input": batch}, timeout=120.0
        )
        elapsed = (time.perf_counter() - start) * 1000  # ms

        if resp.status_code != 200:
            print(f"  Error: {resp.status_code} - {resp.text[:200]}")
            continue

        data = resp.json()
        if "embeddings" not in data:
            print(f"  Warning: No embeddings in response")
            continue

        # Time per text in batch
        times.append(elapsed / len(batch))

    if not times:
        return 0.0, 0.0

    avg_time = sum(times) / len(times)
    throughput = 1000.0 / avg_time if avg_time > 0 else 0.0

    return avg_time, throughput


async def benchmark_search_quality(
    conn: asyncpg.Connection,
    client: httpx.AsyncClient,
    model: str,
    sample_files: List[Dict],
) -> float:
    """Benchmark search quality using sample queries.

    Returns quality score 0.0-1.0 based on relevance of top results.
    """
    # Test queries with expected file types (based on actual DB content)
    test_queries = [
        ("database connection", [".py", ".js", ".ts", ".rs"]),
        ("authentication login", [".py", ".js", ".ts", ".rs"]),
        ("React component", [".js", ".ts", ".tsx"]),
        ("API endpoint", [".py", ".js", ".ts", ".rs"]),
        ("configuration settings", [".json", ".txt", ".md"]),
    ]

    scores = []

    for query, expected_exts in test_queries:
        # Get query embedding
        resp = await client.post(
            OLLAMA_URL, json={"model": model, "input": [query]}, timeout=30.0
        )

        if resp.status_code != 200:
            continue

        data = resp.json()
        if "embeddings" not in data or not data["embeddings"]:
            continue

        query_vec = data["embeddings"][0]

        # Find similar files using vector search
        rows = await conn.fetch(
            """
            SELECT f.id, f.extension
            FROM file_embeddings fe
            JOIN files f ON f.id = fe.file_id
            ORDER BY fe.embedding <=> $1::vector
            LIMIT 10
            """,
            str(query_vec),
        )

        # Score based on extension matches
        if rows:
            matches = sum(1 for r in rows if r["extension"] in expected_exts)
            scores.append(matches / len(rows))

    return sum(scores) / len(scores) if scores else 0.0


async def check_model_available(client: httpx.AsyncClient, model: str) -> bool:
    """Check if model is available in Ollama."""
    try:
        resp = await client.get("http://localhost:11434/api/tags", timeout=10.0)
        if resp.status_code != 200:
            return False

        data = resp.json()
        model_names = [m.get("name", "").lower() for m in data.get("models", [])]
        return model.lower() in model_names or f"{model}:latest".lower() in model_names
    except Exception as e:
        print(f"Error checking model availability: {e}")
        return False


async def run_benchmark(
    models: List[str], num_samples: int = 100
) -> List[BenchmarkResult]:
    """Run complete benchmark suite."""

    results = []

    # Connect to database using individual params (asyncpg needs postgresql:// format)
    conn = await asyncpg.connect(
        host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASS
    )

    try:
        # Fetch sample files
        print(f"Fetching {num_samples} sample files from database...")
        sample_files = await get_sample_files(conn, num_samples)
        texts = [
            f["content_preview"][:500] for f in sample_files if f.get("content_preview")
        ]
        print(f"Loaded {len(texts)} text samples")

        async with httpx.AsyncClient() as client:
            for model in models:
                print(f"\n{'=' * 60}")
                print(f"Benchmarking: {model}")
                print("=" * 60)

                # Check if model available
                if not await check_model_available(client, model):
                    print(f"  Model not available - skipping")
                    results.append(
                        BenchmarkResult(
                            model=model,
                            dimensions=MODEL_SPECS.get(model, {}).get("dimensions", 0),
                            avg_embed_time_ms=0.0,
                            throughput_per_sec=0.0,
                            memory_mb=0.0,
                            search_quality_score=0.0,
                            notes="Model not available",
                        )
                    )
                    continue

                spec = MODEL_SPECS.get(model, {"dimensions": 768})

                # Speed benchmark
                print(f"  Testing embedding speed (batch=32)...")
                avg_time, throughput = await benchmark_embedding_speed(
                    client,
                    model,
                    texts[:50],
                    batch_size=32,  # Use 50 for speed test
                )
                print(f"    Avg time: {avg_time:.2f} ms/text")
                print(f"    Throughput: {throughput:.1f} texts/sec")

                # Memory usage (estimated from model size)
                memory_mb = 0.0
                if model == "nomic-embed-text:latest":
                    memory_mb = 274  # MB from Ollama tags
                elif model == "mxbai-embed-large:latest":
                    memory_mb = 669  # MB
                elif "snowflake" in model:
                    memory_mb = 500  # Estimated
                print(f"    Memory: ~{memory_mb} MB")

                # Quality benchmark
                print(f"  Testing search quality...")
                quality_score = await benchmark_search_quality(
                    conn, client, model, sample_files[:30]
                )
                print(f"    Quality score: {quality_score:.2%}")

                results.append(
                    BenchmarkResult(
                        model=model,
                        dimensions=spec["dimensions"],
                        avg_embed_time_ms=avg_time,
                        throughput_per_sec=throughput,
                        memory_mb=memory_mb,
                        search_quality_score=quality_score,
                        notes=spec.get("description", ""),
                    )
                )

    finally:
        await conn.close()

    return results


def print_comparison_table(results: List[BenchmarkResult]):
    """Print formatted comparison table."""
    print("\n" + "=" * 100)
    print("EMBEDDING MODEL COMPARISON")
    print("=" * 100)
    print(
        f"{'Model':<35} {'Dims':<8} {'Time (ms)':<12} {'Throughput':<14} {'Memory':<10} {'Quality':<10} Notes"
    )
    print("-" * 100)

    for r in results:
        print(
            f"{r.model:<35} {r.dimensions:<8} {r.avg_embed_time_ms:<12.2f} "
            f"{r.throughput_per_sec:<14.1f} {r.memory_mb:<10.0f} "
            f"{r.search_quality_score:<10.2%} {r.notes[:30]}"
        )

    print("=" * 100)

    # Recommendation
    print("\nRECOMMENDATION:")
    valid_results = [r for r in results if r.avg_embed_time_ms > 0]

    if valid_results:
        # Score each model (normalized)
        best = max(
            valid_results,
            key=lambda r: (
                r.search_quality_score * 0.5  # 50% weight on quality
                + min(r.throughput_per_sec / 100, 1.0) * 0.3  # 30% on throughput
                + min(1000 / r.memory_mb, 1.0) * 0.2  # 20% on memory efficiency
            ),
        )
        print(f"  Recommended: {best.model}")
        print(f"    - Quality: {best.search_quality_score:.1%}")
        print(f"    - Speed: {best.throughput_per_sec:.1f} texts/sec")
        print(f"    - Memory: {best.memory_mb:.0f} MB")
    else:
        print("  No valid results available")


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Benchmark embedding models")
    parser.add_argument(
        "--models",
        default="nomic-embed-text:latest",
        help="Comma-separated list of models to benchmark",
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=100,
        help="Number of sample files to use (default: 100)",
    )

    args = parser.parse_args()

    models = [m.strip() for m in args.models.split(",")]

    print("Embedding Model Benchmark")
    print(f"Models: {models}")
    print(f"Samples: {args.samples}")
    print(f"Database: {DB_NAME}")

    results = await run_benchmark(models, args.samples)
    print_comparison_table(results)

    # Save results to JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"benchmark_results_{timestamp}.json"

    with open(output_file, "w") as f:
        json.dump([asdict(r) for r in results], f, indent=2)

    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    asyncio.run(main())

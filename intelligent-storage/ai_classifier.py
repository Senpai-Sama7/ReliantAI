#!/usr/bin/env python3
"""AI Auto-Classification & Smart Tagging

Classifies files using LLM and generates smart tags.
Integrates with indexer and file_watcher.

Usage:
    python3 ai_classifier.py [--file FILE_PATH] [--batch]
"""

import asyncio
import json
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

import httpx
import asyncpg

from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASS
import gemini_client


@dataclass
class ClassificationResult:
    """Result from AI classification."""

    category: str
    tags: List[str]
    confidence: float
    raw_response: str


async def classify_file(
    client: httpx.AsyncClient, filename: str, extension: str, content_preview: str
) -> Optional[ClassificationResult]:
    """Classify a file using AI.

    Returns classification with category and tags.
    """
    # Prepare prompt
    preview = (content_preview or "")[:1000]  # Limit preview length

    prompt = f"""Classify this file and suggest relevant tags.

Filename: {filename}
Extension: {extension}
Content Preview:
{preview}

Respond ONLY with JSON in this exact format:
{{
  "category": "brief category like 'Python Script', 'Config File', 'Documentation'",
  "tags": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "confidence": 0.85
}}

Rules:
- Category should be 2-3 words max
- Tags should be 3-5 relevant keywords
- Confidence is 0.0-1.0 based on content clarity
- Be specific: "API Router" not "Code"
- Include file type: "Python", "JavaScript", "Markdown" etc.
"""

    try:
        response_text = await gemini_client.generate(prompt, temperature=0.3)

        if not response_text:
            print("Classification error: empty response")
            return None

        # Extract JSON from response
        json_match = re.search(r"\{[^}]+\}", response_text, re.DOTALL)
        if not json_match:
            # Try to parse the whole response
            json_match = re.search(r"\{.*\}", response_text, re.DOTALL)

        if json_match:
            try:
                result = json.loads(json_match.group())
                return ClassificationResult(
                    category=result.get("category", "Unknown"),
                    tags=result.get("tags", []),
                    confidence=float(result.get("confidence", 0.5)),
                    raw_response=response_text,
                )
            except json.JSONDecodeError:
                pass

        # Fallback: parse manually
        category = extract_field(response_text, "category") or "Unknown"
        tags = extract_tags(response_text)
        confidence = extract_confidence(response_text)

        return ClassificationResult(
            category=category,
            tags=tags,
            confidence=confidence,
            raw_response=response_text,
        )

    except Exception as e:
        print(f"Classification error: {e}")
        return None


def extract_field(text: str, field: str) -> Optional[str]:
    """Extract a field value from text."""
    patterns = [
        rf'"{field}"\s*:\s*"([^"]+)"',
        rf'{field}\s*:\s*"([^"]+)"',
        rf"{field}\s*:\s*([^\n,]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def extract_tags(text: str) -> List[str]:
    """Extract tags from text."""
    # Look for tags array
    match = re.search(r'"tags"\s*:\s*\[([^\]]+)\]', text, re.DOTALL)
    if match:
        tags_text = match.group(1)
        # Extract quoted strings
        tags = re.findall(r'"([^"]+)"', tags_text)
        return tags[:5]  # Max 5 tags
    return []


def extract_confidence(text: str) -> float:
    """Extract confidence score from text."""
    match = re.search(r'"confidence"\s*:\s*(0?\.\d+|1\.0?)', text)
    if match:
        return float(match.group(1))
    return 0.5


async def store_classification(
    conn: asyncpg.Connection, file_id: int, classification: ClassificationResult
):
    """Store classification results in database."""

    # Store category as a tag
    category_tag = classification.category.lower().replace(" ", "_")

    # Combine category with tags
    all_tags = [category_tag] + classification.tags

    for tag_name in all_tags:
        # Insert tag if not exists
        tag_id = await conn.fetchval(
            """
            INSERT INTO tags (name) VALUES ($1)
            ON CONFLICT (name) DO UPDATE SET name = $1
            RETURNING id
            """,
            tag_name.lower(),
        )

        # Link tag to file
        await conn.execute(
            """
            INSERT INTO file_tags (file_id, tag_id, confidence, source)
            VALUES ($1, $2, $3, 'ai')
            ON CONFLICT (file_id, tag_id) DO UPDATE
            SET confidence = $3, source = 'ai'
            """,
            file_id,
            tag_id,
            classification.confidence,
        )

    # Update file metadata with category
    await conn.execute(
        """
        UPDATE files 
        SET metadata = COALESCE(metadata, '{}'::jsonb) || $1::jsonb
        WHERE id = $2
        """,
        json.dumps(
            {
                "ai_category": classification.category,
                "ai_tags": classification.tags,
                "ai_confidence": classification.confidence,
            }
        ),
        file_id,
    )


async def classify_single_file(file_path: str) -> Optional[ClassificationResult]:
    """Classify a single file by path."""
    from pathlib import Path

    path = Path(file_path)
    if not path.exists():
        print(f"File not found: {file_path}")
        return None

    # Read preview
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            preview = f.read(2000)
    except Exception as e:
        print(f"Error reading file: {e}")
        preview = ""

    async with httpx.AsyncClient() as client:
        result = await classify_file(client, path.name, path.suffix.lower(), preview)

    return result


async def batch_classify_files(conn: asyncpg.Connection, limit: int = 10) -> Dict:
    """Classify files that don't have AI tags yet."""

    # Find files without AI classification
    rows = await conn.fetch(
        """
        SELECT f.id, f.name, f.extension, f.content_preview
        FROM files f
        LEFT JOIN file_tags ft ON f.id = ft.file_id AND ft.source = 'ai'
        WHERE ft.file_id IS NULL
          AND f.content_preview IS NOT NULL
        ORDER BY f.updated_at DESC
        LIMIT $1
        """,
        limit,
    )

    if not rows:
        print("No files need classification")
        return {"classified": 0, "failed": 0}

    print(f"Classifying {len(rows)} files...")

    stats = {"classified": 0, "failed": 0}

    async with httpx.AsyncClient() as client:
        for row in rows:
            print(f"  {row['name']}...", end=" ")

            classification = await classify_file(
                client, row["name"], row["extension"], row["content_preview"]
            )

            if classification:
                await store_classification(conn, row["id"], classification)
                print(f"✓ {classification.category}")
                stats["classified"] += 1
            else:
                print("✗ failed")
                stats["failed"] += 1

    return stats


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="AI File Classification")
    parser.add_argument("--file", help="Classify a single file")
    parser.add_argument("--batch", action="store_true", help="Classify batch of files")
    parser.add_argument("--limit", type=int, default=10, help="Batch limit")

    args = parser.parse_args()

    if args.file:
        # Single file classification
        result = await classify_single_file(args.file)
        if result:
            print(f"\nClassification Results:")
            print(f"  Category: {result.category}")
            print(f"  Tags: {', '.join(result.tags)}")
            print(f"  Confidence: {result.confidence:.1%}")
        else:
            print("Classification failed")

    elif args.batch:
        # Batch classification
        conn = await asyncpg.connect(
            host=DB_HOST, port=DB_PORT, database=DB_NAME, user=DB_USER, password=DB_PASS
        )

        try:
            stats = await batch_classify_files(conn, args.limit)
            print(f"\nBatch complete: {stats}")
        finally:
            await conn.close()

    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())

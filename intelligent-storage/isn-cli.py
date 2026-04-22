#!/usr/bin/env python3
"""ISN CLI — Intelligent Storage Nexus command-line query tool.

Usage:
    isn-cli.py search "react authentication hooks"
    isn-cli.py search "network config" --tag python --ext .py
    isn-cli.py search "database schema" --type sql --limit 5
    isn-cli.py ask "which files handle JWT token refresh?"
    isn-cli.py remember "The auth module was refactored on 2026-02-20"
    isn-cli.py recall "auth refactor"
"""

import argparse
import json
import sys
import textwrap

import psycopg2
import psycopg2.extras
import requests

# --- Config (mirrors config.py defaults) ---
DB_DSN = "postgresql://storage_admin:storage_local_2026@localhost:5433/intelligent_storage"
OLLAMA_EMBED_URL = "http://localhost:11434/api/embed"
OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
EMBED_MODEL = "nomic-embed-text"
CHAT_MODEL = "qwen3-8b-hivemind-uncensored"
EMBED_DIM = 768


def get_embedding(text: str) -> list[float]:
    """Get embedding vector from Ollama."""
    resp = requests.post(OLLAMA_EMBED_URL, json={"model": EMBED_MODEL, "input": text}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # Ollama returns {"embeddings": [[...]]} for /api/embed
    emb = data.get("embeddings") or data.get("embedding")
    if isinstance(emb, list) and emb and isinstance(emb[0], list):
        return emb[0]
    return emb


def ollama_chat(system_prompt: str, user_msg: str) -> str:
    """Single-turn chat with Ollama."""
    resp = requests.post(OLLAMA_CHAT_URL, json={
        "model": CHAT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ],
        "stream": False,
    }, timeout=120)
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def connect_db():
    """Return a psycopg2 connection."""
    conn = psycopg2.connect(DB_DSN)
    psycopg2.extras.register_default_jsonb(conn)
    return conn


# ── Search ──────────────────────────────────────────────────────────────

def cmd_search(args):
    """Hybrid search with optional tag/ext/type filters."""
    query = " ".join(args.query)
    embedding = get_embedding(query)
    emb_literal = "[" + ",".join(str(v) for v in embedding) + "]"

    conn = connect_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    # Base hybrid search via the DB function
    sql = """
        SELECT h.file_id, h.file_path, h.file_name, h.score,
               h.semantic_score, h.keyword_score
        FROM hybrid_search(%s::text, %s::vector, %s::int) h
    """
    params: list = [query, emb_literal, args.limit * 3]  # overfetch for post-filter

    # Post-filter with JOINs for tag/ext/type
    filters = []
    if args.tag:
        sql = f"""
            SELECT h.file_id, h.file_path, h.file_name, h.score,
                   h.semantic_score, h.keyword_score
            FROM hybrid_search(%s::text, %s::vector, %s::int) h
            JOIN file_tags ft ON ft.file_id = h.file_id
            JOIN tags t ON t.id = ft.tag_id AND t.name = %s
        """
        params.append(args.tag)
    if args.ext:
        ext = args.ext if args.ext.startswith(".") else f".{args.ext}"
        filters.append(("h.file_path LIKE %s", f"%{ext}"))
    if args.type:
        filters.append(("h.file_path LIKE %s", f"%.{args.type}"))

    if filters:
        where_clauses = " AND ".join(f[0] for f in filters)
        sql += f" WHERE {where_clauses}"
        params.extend(f[1] for f in filters)

    sql += " ORDER BY h.score DESC LIMIT %s"
    params.append(args.limit)

    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if args.json:
        print(json.dumps([dict(r) for r in rows], indent=2, default=str))
        return

    if not rows:
        print("No results found.")
        return

    print(f"\n{'#':>3}  {'Score':>6}  {'Sem':>5}  {'KW':>5}  Path")
    print("─" * 80)
    for i, r in enumerate(rows, 1):
        print(f"{i:>3}  {r['score']:>6.3f}  {r['semantic_score']:>5.3f}  "
              f"{r['keyword_score']:>5.3f}  {r['file_path']}")
    print(f"\n{len(rows)} results for: \"{query}\"")


# ── Ask (NL query) ─────────────────────────────────────────────────────

def cmd_ask(args):
    """Natural language query: LLM interprets the question, searches, summarizes."""
    question = " ".join(args.query)

    # Step 1: Extract search terms from the question
    search_terms = ollama_chat(
        "You are a search query extractor. Given a natural language question about files "
        "on a storage system, output ONLY the 2-5 most relevant search keywords separated "
        "by spaces. No explanation, no punctuation, just keywords.",
        question,
    ).strip()
    # Strip any /think tags from reasoning models
    if "</think>" in search_terms:
        search_terms = search_terms.split("</think>")[-1].strip()

    print(f"🔍 Searching: {search_terms}")

    # Step 2: Hybrid search with extracted terms
    embedding = get_embedding(search_terms)
    emb_literal = "[" + ",".join(str(v) for v in embedding) + "]"

    conn = connect_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT h.file_id, h.file_path, h.file_name, h.score "
        "FROM hybrid_search(%s::text, %s::vector, %s::int) h ORDER BY h.score DESC LIMIT %s",
        [search_terms, emb_literal, 10, 10],
    )
    rows = cur.fetchall()

    # Step 3: Fetch content previews for top results
    if rows:
        ids = [r["file_id"] for r in rows[:5]]
        cur.execute(
            "SELECT id, path, content_preview FROM files WHERE id = ANY(%s)",
            (ids,),
        )
        previews = {r["id"]: r for r in cur.fetchall()}
    else:
        previews = {}

    cur.close()
    conn.close()

    if not rows:
        print("No relevant files found.")
        return

    # Step 4: LLM summarizes the results
    context = "\n\n".join(
        f"File: {r['file_path']}\nPreview: {previews.get(r['file_id'], {}).get('content_preview', 'N/A')[:300]}"
        for r in rows[:5]
    )

    answer = ollama_chat(
        "You are a helpful file system assistant. Given search results from a storage index, "
        "answer the user's question concisely. Reference specific file paths. "
        "If the results don't answer the question, say so.",
        f"Question: {question}\n\nSearch Results:\n{context}",
    )
    # Strip think tags
    if "</think>" in answer:
        answer = answer.split("</think>")[-1].strip()

    print(f"\n{answer}")
    print(f"\n📁 Top files:")
    for r in rows[:5]:
        print(f"  {r['score']:.3f}  {r['file_path']}")


# ── Memory ──────────────────────────────────────────────────────────────

def cmd_remember(args):
    """Store a memory for the agent."""
    content = " ".join(args.content)
    embedding = get_embedding(content)
    emb_literal = "[" + ",".join(str(v) for v in embedding) + "]"

    conn = connect_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO agent_memories (agent_id, memory_type, content, embedding, importance) "
        "VALUES (%s, %s, %s, %s::vector, %s) RETURNING id",
        [args.agent_id, args.memory_type, content, emb_literal, args.importance],
    )
    mem_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Memory stored (id={mem_id}, agent={args.agent_id}, type={args.memory_type})")


def cmd_recall(args):
    """Recall memories by semantic similarity."""
    query = " ".join(args.query)
    embedding = get_embedding(query)
    emb_literal = "[" + ",".join(str(v) for v in embedding) + "]"

    conn = connect_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT * FROM recall_memories(%s, %s::vector, %s)",
        [args.agent_id, emb_literal, args.limit],
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()

    if args.json:
        print(json.dumps([dict(r) for r in rows], indent=2, default=str))
        return

    if not rows:
        print("No memories found.")
        return

    for r in rows:
        print(f"\n[{r['memory_type']}] (relevance={r['relevance']:.3f}, importance={r['importance']:.1f})")
        print(textwrap.fill(r["content"], width=100))
    print(f"\n{len(rows)} memories recalled for: \"{query}\"")


# ── CLI ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="isn-cli",
        description="Intelligent Storage Nexus — CLI query tool",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # search
    p_search = sub.add_parser("search", help="Hybrid search (semantic + keyword + trigram)")
    p_search.add_argument("query", nargs="+", help="Search query")
    p_search.add_argument("--tag", help="Filter by tag name")
    p_search.add_argument("--ext", help="Filter by file extension (e.g. .py)")
    p_search.add_argument("--type", help="Filter by file type/extension (e.g. sql)")
    p_search.add_argument("--limit", type=int, default=15, help="Max results (default: 15)")
    p_search.add_argument("--json", action="store_true", help="Output as JSON")
    p_search.set_defaults(func=cmd_search)

    # ask
    p_ask = sub.add_parser("ask", help="Natural language query (uses LLM)")
    p_ask.add_argument("query", nargs="+", help="Question in natural language")
    p_ask.set_defaults(func=cmd_ask)

    # remember
    p_rem = sub.add_parser("remember", help="Store a memory")
    p_rem.add_argument("content", nargs="+", help="Memory content")
    p_rem.add_argument("--agent-id", default="cli", help="Agent ID (default: cli)")
    p_rem.add_argument("--memory-type", default="observation", help="Memory type (default: observation)")
    p_rem.add_argument("--importance", type=float, default=0.5, help="Importance 0-1 (default: 0.5)")
    p_rem.set_defaults(func=cmd_remember)

    # recall
    p_rec = sub.add_parser("recall", help="Recall memories by semantic similarity")
    p_rec.add_argument("query", nargs="+", help="Recall query")
    p_rec.add_argument("--agent-id", default="cli", help="Agent ID (default: cli)")
    p_rec.add_argument("--limit", type=int, default=5, help="Max memories (default: 5)")
    p_rec.add_argument("--json", action="store_true", help="Output as JSON")
    p_rec.set_defaults(func=cmd_recall)

    args = parser.parse_args()
    try:
        args.func(args)
    except requests.ConnectionError:
        print("❌ Cannot connect to Ollama. Is it running? (http://localhost:11434)", file=sys.stderr)
        sys.exit(1)
    except requests.ReadTimeout:
        print("❌ Ollama request timed out. The model may be loading or the query too complex.", file=sys.stderr)
        sys.exit(1)
    except psycopg2.OperationalError as e:
        print(f"❌ Database connection failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

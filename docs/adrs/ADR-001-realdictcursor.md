# ADR-001: Use `psycopg2.extras.RealDictCursor` as Mandatory Cursor Factory

## Status
Accepted (2024-01-15)

## Context
The ReliantAI platform uses `psycopg2` for PostgreSQL connectivity across all Python
services (Money, ComplianceOne, FinOps360, integration). By default, `psycopg2`
returns rows as tuples, and developers were converting them to dicts with `dict(row)`.

### Problem
```python
# BAD — crashes
row = cursor.fetchone()
data = dict(row)  # TypeError: 'tuple' object is not callable
# or
for row in cursor.fetchall():
    print(row["name"])  # TypeError: tuple indices must be integers or slices
```

This pattern caused runtime crashes in ComplianceOne (line 209) and FinOps360 (line 339)
when developers forgot that `cursor_factory` was not set, and code that expected
dict-like access received tuples instead.

## Decision
All PostgreSQL connections **must** use `cursor_factory=RealDictCursor`:

```python
from psycopg2.extras import RealDictCursor
conn = psycopg2.connect(dsn=DATABASE_URL, cursor_factory=RealDictCursor)
# or
pool = psycopg2.pool.ThreadedConnectionPool(1, 20, dsn=DATABASE_URL)
# then use cursor_factory in individual cursor() calls
with conn.cursor(cursor_factory=RealDictCursor) as cur:
    cur.execute("SELECT * FROM dispatches")
    for row in cur.fetchall():
        print(row["customer_name"])  # Works — row is dict-like
```

## Consequences

### Positive
- **Eliminates `dict(row)` crashes** — rows are natively dict-like.
- **Faster JSON serialization** — `json.dumps(row)` works directly.
- **Clearer code** — `row["column_name"]` is self-documenting vs `row[3]`.
- **Easier validation** — Pydantic models can consume dicts directly.

### Negative
- **Slight memory overhead** — `RealDictCursor` stores column names per row.
- **Dependency on `psycopg2.extras`** — must be imported explicitly.
- **Cannot use tuple unpacking** — `id, name = row` fails; must use `row["id"]`.

## Mitigation
- Static analysis (flake8 + custom AST check) verifies `cursor_factory=RealDictCursor`
  is present in all `.cursor()` calls.
- `AGENTS.md` documents this as a "Systemic Invariant — NEVER BREAK".

## Alternatives Considered
- **NamedTupleCursor**: Rejected — less flexible than dicts for JSON serialization.
- **Custom RowFactory**: Rejected — unnecessary complexity; RealDictCursor is battle-tested.
- **SQLAlchemy ORM**: Rejected — adds heavy dependency; platform uses raw SQL for performance.

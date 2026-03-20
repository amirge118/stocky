"""
migrate_to_supabase.py — Copy all data from a source PostgreSQL database to
a target Supabase PostgreSQL database using asyncpg directly (no SQLAlchemy).

Usage:
    SOURCE_DATABASE_URL="postgresql://user:pass@localhost:5432/stock_insight" \
    TARGET_DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres" \
    python migrate_to_supabase.py

Both env vars can also be passed as CLI args:
    python migrate_to_supabase.py <source_url> <target_url>

Requirements:
    pip install asyncpg

The script is idempotent: every INSERT uses ON CONFLICT DO NOTHING so re-running
it is safe. After each table it resets the PostgreSQL sequence so future inserts
do not collide with migrated IDs.
"""

import asyncio
import os
import sys
from typing import Any

try:
    import asyncpg
except ImportError:
    sys.exit("asyncpg is required.  Run:  pip install asyncpg")


# ---------------------------------------------------------------------------
# Table migration order (dependencies first)
# ---------------------------------------------------------------------------
TABLES = [
    "stocks",
    "holdings",
    "agent_reports",
    "alerts",
    "watchlist_lists",
    "watchlist_items",  # FK → watchlist_lists
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_driver(url: str) -> str:
    """Strip SQLAlchemy driver prefix so asyncpg can use the URL directly."""
    for prefix in ("postgresql+asyncpg://", "postgresql+psycopg2://"):
        if url.startswith(prefix):
            return "postgresql://" + url[len(prefix):]
    return url


async def fetch_all_rows(conn: asyncpg.Connection, table: str) -> list[dict[str, Any]]:
    rows = await conn.fetch(f"SELECT * FROM {table} ORDER BY id")
    return [dict(r) for r in rows]


async def insert_rows(
    conn: asyncpg.Connection,
    table: str,
    rows: list[dict[str, Any]],
) -> int:
    if not rows:
        return 0

    columns = list(rows[0].keys())
    col_list = ", ".join(f'"{c}"' for c in columns)
    placeholders = ", ".join(f"${i + 1}" for i in range(len(columns)))

    query = (
        f"INSERT INTO {table} ({col_list}) "
        f"VALUES ({placeholders}) "
        f"ON CONFLICT DO NOTHING"
    )

    inserted = 0
    for row in rows:
        values = [row[c] for c in columns]
        result = await conn.execute(query, *values)
        # result string is like "INSERT 0 1" or "INSERT 0 0"
        inserted += int(result.split()[-1])

    return inserted


async def reset_sequence(conn: asyncpg.Connection, table: str) -> None:
    """Set the table's id sequence to max(id) so auto-increment works after insert."""
    await conn.execute(
        f"""
        SELECT setval(
            pg_get_serial_sequence('{table}', 'id'),
            COALESCE((SELECT MAX(id) FROM {table}), 0) + 1,
            false
        )
        """
    )


# ---------------------------------------------------------------------------
# Main migration logic
# ---------------------------------------------------------------------------

async def migrate(source_url: str, target_url: str) -> None:
    print("Connecting to source database …")
    src = await asyncpg.connect(source_url)

    print("Connecting to target database …")
    tgt = await asyncpg.connect(target_url)

    summary: list[tuple[str, int, int]] = []  # (table, fetched, inserted)

    try:
        for table in TABLES:
            print(f"\n  [{table}]")

            # Check source table exists
            exists = await src.fetchval(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = $1)",
                table,
            )
            if not exists:
                print(f"    ⚠  Table not found in source — skipping")
                summary.append((table, 0, 0))
                continue

            rows = await fetch_all_rows(src, table)
            print(f"    Fetched {len(rows)} rows from source")

            if rows:
                inserted = await insert_rows(tgt, table, rows)
                await reset_sequence(tgt, table)
                print(f"    Inserted {inserted} rows into target")
            else:
                inserted = 0
                print(f"    Nothing to migrate")

            summary.append((table, len(rows), inserted))

    finally:
        await src.close()
        await tgt.close()

    # ---------------------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------------------
    print("\n" + "=" * 55)
    print(f"{'Table':<25} {'Fetched':>10} {'Inserted':>10}")
    print("-" * 55)
    total_fetched = total_inserted = 0
    for table, fetched, inserted in summary:
        skipped = fetched - inserted
        note = f"  ({skipped} skipped/already existed)" if skipped else ""
        print(f"  {table:<23} {fetched:>10} {inserted:>10}{note}")
        total_fetched += fetched
        total_inserted += inserted
    print("-" * 55)
    print(f"  {'TOTAL':<23} {total_fetched:>10} {total_inserted:>10}")
    print("=" * 55)
    print("\nMigration complete.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    args = sys.argv[1:]

    if len(args) == 2:
        source_url, target_url = args
    else:
        source_url = os.environ.get("SOURCE_DATABASE_URL", "")
        target_url = os.environ.get("TARGET_DATABASE_URL", "")

    if not source_url:
        sys.exit(
            "Error: SOURCE_DATABASE_URL env var (or first CLI arg) is required.\n"
            "Example:\n"
            "  SOURCE_DATABASE_URL='postgresql://user:pass@localhost:5432/db' \\\n"
            "  TARGET_DATABASE_URL='postgresql://postgres:pass@db.xxx.supabase.co:5432/postgres' \\\n"
            "  python migrate_to_supabase.py"
        )
    if not target_url:
        sys.exit("Error: TARGET_DATABASE_URL env var (or second CLI arg) is required.")

    source_url = _strip_driver(source_url)
    target_url = _strip_driver(target_url)

    asyncio.run(migrate(source_url, target_url))


if __name__ == "__main__":
    main()

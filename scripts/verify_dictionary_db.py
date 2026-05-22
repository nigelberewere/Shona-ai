"""Quick sanity check for the rebuilt dictionary database."""

from __future__ import annotations

import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "database" / "duramazwi.db"


def resolve_db_path(path: Path) -> Path:
    if path.exists():
        return path
    alt = path.with_name(path.stem + "_rebuild" + path.suffix)
    return alt


def main() -> None:
    try:
        connection = sqlite3.connect(DB_PATH)
        header = connection.execute("PRAGMA schema_version").fetchone()[0]
        count = connection.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        sample = connection.execute(
            "SELECT word, source, record_type FROM entries ORDER BY word LIMIT 5"
        ).fetchall()
        db = DB_PATH
        connection.close()
    except sqlite3.DatabaseError:
        alt = DB_PATH.with_name(DB_PATH.stem + "_rebuild" + DB_PATH.suffix)
        connection = sqlite3.connect(alt)
        header = connection.execute("PRAGMA schema_version").fetchone()[0]
        count = connection.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        sample = connection.execute(
            "SELECT word, source, record_type FROM entries ORDER BY word LIMIT 5"
        ).fetchall()
        db = alt
        connection.close()
    print(f"database_path={db}")
    print(f"schema_version={header}")
    print(f"entries={count}")
    for row in sample:
        print(" | ".join(row))


if __name__ == "__main__":
    main()

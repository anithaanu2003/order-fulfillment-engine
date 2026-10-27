
from pathlib import Path
import sqlite3

# Project root is the parent of the src directory.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

SCHEMA_FILE = PROJECT_ROOT / "sql" / "schema.sql"
DATABASE_FILE = PROJECT_ROOT / "data" / "fulfillment.db"


def initialize_database():
    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(
            f"Schema file not found: {SCHEMA_FILE}"
        )

    DATABASE_FILE.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DATABASE_FILE) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        schema = SCHEMA_FILE.read_text(encoding="utf-8")
        connection.executescript(schema)

        foreign_keys_enabled = connection.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]

        if foreign_keys_enabled != 1:
            raise RuntimeError("Foreign-key enforcement is disabled.")

        tables = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            ORDER BY name
            """
        ).fetchall()

    print("Database initialized successfully!")
    print(f"Database location: {DATABASE_FILE}")
    print("Tables created:")

    for (table_name,) in tables:
        print(f"- {table_name}")


if __name__ == "__main__":
    initialize_database()

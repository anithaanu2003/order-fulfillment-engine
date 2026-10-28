import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "fulfillment.db"

connection = sqlite3.connect(
    DATABASE_PATH.as_uri() + "?mode=ro",
    uri=True,
)

try:
    tables = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        ORDER BY name
        """
    ).fetchall()

    print("Database tables:")
    for (table_name,) in tables:
        print(f"- {table_name}")

    table_names = {name for (name,) in tables}

    print(
        "\nCalendar tables present:",
        {"holidays", "carrier_calendars"}.issubset(table_names),
    )
finally:
    connection.close()
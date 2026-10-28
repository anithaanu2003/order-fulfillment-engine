
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "fulfillment.db"

connection = sqlite3.connect(
    DATABASE_PATH.as_uri() + "?mode=ro",
    uri=True,
)

try:
    checks = {
        "Orders": "SELECT COUNT(*) FROM orders",
        "Order lines": "SELECT COUNT(*) FROM order_lines",
        "Holiday records": "SELECT COUNT(*) FROM holidays",
        "Carrier calendar records": (
            "SELECT COUNT(*) FROM carrier_calendars"
        ),
        "Active holidays": (
            "SELECT COUNT(*) FROM holidays WHERE is_active = 1"
        ),
        "Operating carrier days": (
            "SELECT COUNT(*) FROM carrier_calendars "
            "WHERE is_operating = 1"
        ),
        "Non-operating carrier days": (
            "SELECT COUNT(*) FROM carrier_calendars "
            "WHERE is_operating = 0"
        ),
    }

    print("Calendar Data Verification")
    print("-" * 36)

    for label, query in checks.items():
        count = connection.execute(query).fetchone()[0]
        print(f"{label}: {count:,}")

    print("\nHoliday records:")
    rows = connection.execute(
        """
        SELECT holiday_date, holiday_name, service_zone, node_id
        FROM holidays
        ORDER BY holiday_date, holiday_id
        """
    ).fetchall()

    for row in rows:
        print(row)

    foreign_key_errors = connection.execute(
        "PRAGMA foreign_key_check"
    ).fetchall()

    print("\nForeign-key violations:", len(foreign_key_errors))

finally:
    connection.close()

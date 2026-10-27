
from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_FILE = PROJECT_ROOT / "data" / "fulfillment.db"

REQUIRED_TABLES = {
    "skus",
    "fulfillment_nodes",
    "carriers",
    "orders",
    "order_lines",
    "inventory",
    "warehouse_capacity",
    "service_levels",
    "carrier_service_zones",
    "shipments",
    "shipment_lines",
    "tracking_events",
    "delivery_promises",
}


def validate_schema():
    if not DATABASE_FILE.exists():
        raise FileNotFoundError(
            f"Database not found: {DATABASE_FILE}"
        )

    with sqlite3.connect(DATABASE_FILE) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        actual_tables = {
            row[0]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            ).fetchall()
        }

        missing_tables = REQUIRED_TABLES - actual_tables

        if missing_tables:
            raise RuntimeError(
                f"Missing tables: {sorted(missing_tables)}"
            )

        foreign_keys_enabled = connection.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0]

        if foreign_keys_enabled != 1:
            raise RuntimeError(
                "Foreign-key enforcement is disabled."
            )

        foreign_key_errors = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        if foreign_key_errors:
            raise RuntimeError(
                f"Foreign-key violations: {foreign_key_errors}"
            )

    print("PASS: All required tables exist.")
    print(f"PASS: Verified {len(REQUIRED_TABLES)} required tables.")
    print("PASS: Foreign-key enforcement is enabled.")
    print("PASS: No foreign-key violations found.")


if __name__ == "__main__":
    validate_schema()

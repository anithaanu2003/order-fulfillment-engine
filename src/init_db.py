
from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SCHEMA_FILE = PROJECT_ROOT / "sql" / "schema.sql"
DATABASE_FILE = PROJECT_ROOT / "data" / "fulfillment.db"

EXPECTED_TABLES = {
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
    "carrier_scans",
    "holidays",
    "carrier_calendars",
}


def initialize_database(database_file=None):
    """Create missing tables and preserve existing data."""

    if not SCHEMA_FILE.exists():
        raise FileNotFoundError(
            f"Schema file not found: {SCHEMA_FILE}"
        )

    target_database = (
        Path(database_file)
        if database_file is not None
        else DATABASE_FILE
    )

    if not target_database.is_absolute():
        target_database = PROJECT_ROOT / target_database

    target_database.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    schema = SCHEMA_FILE.read_text(encoding="utf-8")

    # Execute each SQL statement separately inside one transaction.
    # The schema contains no triggers, stored procedures, or
    # semicolons inside string literals.
    statements = [
        statement.strip()
        for statement in schema.split(";")
        if statement.strip()
        and not all(
            line.strip().startswith("--")
            for line in statement.splitlines()
            if line.strip()
        )
    ]

    connection = sqlite3.connect(target_database)

    try:
        connection.execute("PRAGMA foreign_keys = ON")

        if connection.execute(
            "PRAGMA foreign_keys"
        ).fetchone()[0] != 1:
            raise RuntimeError(
                "Could not enable foreign-key enforcement."
            )

        connection.execute("BEGIN")

        for statement in statements:
            # Ignore standalone SQL comments.
            sql_lines = [
                line
                for line in statement.splitlines()
                if not line.strip().startswith("--")
            ]
            sql_statement = "\n".join(sql_lines).strip()

            if sql_statement:
                connection.execute(sql_statement)

        tables = {
            row[0]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            ).fetchall()
        }

        missing_tables = EXPECTED_TABLES - tables

        if missing_tables:
            raise RuntimeError(
                "Missing expected tables: "
                + ", ".join(sorted(missing_tables))
            )

        foreign_key_errors = connection.execute(
            "PRAGMA foreign_key_check"
        ).fetchall()

        if foreign_key_errors:
            raise RuntimeError(
                "Foreign-key violations detected: "
                f"{len(foreign_key_errors)}"
            )

        order_count = connection.execute(
            "SELECT COUNT(*) FROM orders"
        ).fetchone()[0]

        order_line_count = connection.execute(
            "SELECT COUNT(*) FROM order_lines"
        ).fetchone()[0]

        connection.commit()

        print("Database schema verified successfully.")
        print(f"Database: {target_database}")
        print(f"Expected tables found: {len(EXPECTED_TABLES)}")
        print(f"Existing orders preserved: {order_count:,}")
        print(f"Existing order lines preserved: {order_line_count:,}")
        print("\nTables:")

        for table_name in sorted(EXPECTED_TABLES):
            print(f"- {table_name}")

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()

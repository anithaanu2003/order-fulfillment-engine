
from pathlib import Path
from datetime import date, timedelta
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_FILE = PROJECT_ROOT / "data" / "fulfillment.db"

START_DATE = "2026-10-01"
END_DATE = "2026-12-31"

INITIAL_CAPACITY = {
    "FUL-2026-000001": (100, 20, 500, 100),
    "FUL-2026-000002": (80, 15, 400, 75),
    "FUL-2026-000003": (70, 10, 350, 60),
}


def generate_capacity_records(nodes):
    records = []
    start_date = date.fromisoformat(START_DATE)
    end_date = date.fromisoformat(END_DATE)

    for sequence, (node_id,) in enumerate(nodes, start=1):
        if node_id in INITIAL_CAPACITY:
            max_lines, initial_used_lines, max_units, initial_used_units = (
                INITIAL_CAPACITY[node_id]
            )
        else:
            max_lines = 80
            initial_used_lines = 0
            max_units = 400
            initial_used_units = 0

        current_date = start_date

        while current_date <= end_date:
            capacity_date = current_date.isoformat()
            capacity_id = (
                f"CAP-{sequence:06d}-{capacity_date.replace('-', '')}"
            )

            if capacity_date == "2026-10-26":
                used_lines = initial_used_lines
                used_units = initial_used_units
            else:
                used_lines = 0
                used_units = 0

            records.append(
                (
                    capacity_id,
                    node_id,
                    capacity_date,
                    max_lines,
                    used_lines,
                    max_units,
                    used_units,
                )
            )

            current_date += timedelta(days=1)

    return records


def seed_capacity(database_file=None):
    target_database = (
        Path(database_file)
        if database_file is not None
        else DATABASE_FILE
    )

    if not target_database.is_absolute():
        target_database = PROJECT_ROOT / target_database

    if not target_database.is_file():
        raise FileNotFoundError(
            f"Database not found: {target_database}. "
            "Initialize the database and seed master data first."
        )

    with sqlite3.connect(target_database) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        nodes = connection.execute(
            "SELECT node_id FROM fulfillment_nodes ORDER BY node_id"
        ).fetchall()

        if len(nodes) != 20:
            raise ValueError(
                f"Expected 20 fulfillment nodes, found {len(nodes)}. "
                "Seed master data first."
            )

        capacity_records = generate_capacity_records(nodes)

        connection.executemany(
            """
            INSERT OR IGNORE INTO warehouse_capacity (
                capacity_id,
                node_id,
                capacity_date,
                max_order_lines,
                used_order_lines,
                max_units,
                used_units
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            capacity_records,
        )

        total_records = connection.execute(
            "SELECT COUNT(*) FROM warehouse_capacity"
        ).fetchone()[0]

        daily_counts = connection.execute(
            """
            SELECT capacity_date, COUNT(*)
            FROM warehouse_capacity
            GROUP BY capacity_date
            ORDER BY capacity_date
            """
        ).fetchall()

    print(f"Database: {target_database}")
    print(f"Total capacity records: {total_records}")
    print("Capacity records by date:")

    for row in daily_counts:
        print(row)


if __name__ == "__main__":
    seed_capacity()

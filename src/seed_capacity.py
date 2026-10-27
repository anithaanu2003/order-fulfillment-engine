
from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_FILE = PROJECT_ROOT / "data" / "fulfillment.db"


def seed_capacity():
    capacity_records = [
        ("CAP-000001", "FUL-2026-000001", "2026-10-26", 100, 20, 500, 100),
        ("CAP-000002", "FUL-2026-000002", "2026-10-26", 80, 15, 400, 75),
        ("CAP-000003", "FUL-2026-000003", "2026-10-26", 70, 10, 350, 60),
    ]

    with sqlite3.connect(DATABASE_FILE) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

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

        rows = connection.execute(
            """
            SELECT
                n.node_name,
                wc.capacity_date,
                wc.max_order_lines,
                wc.used_order_lines,
                wc.max_order_lines - wc.used_order_lines
                    AS remaining_order_lines,
                wc.max_units,
                wc.used_units,
                wc.max_units - wc.used_units
                    AS remaining_units
            FROM warehouse_capacity AS wc
            JOIN fulfillment_nodes AS n
                ON wc.node_id = n.node_id
            ORDER BY n.node_name
            """
        ).fetchall()

    print(f"Warehouse capacity records found: {len(rows)}")
    print("\nWarehouse capacity:")

    for row in rows:
        print(row)


if __name__ == "__main__":
    seed_capacity()

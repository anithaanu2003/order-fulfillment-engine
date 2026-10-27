
from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_FILE = PROJECT_ROOT / "data" / "fulfillment.db"

CAPACITY_DATE = "2026-10-26"

INITIAL_CAPACITY = {
    "FUL-2026-000001": (100, 20, 500, 100),
    "FUL-2026-000002": (80, 15, 400, 75),
    "FUL-2026-000003": (70, 10, 350, 60),
}


def generate_capacity_records(nodes):
    records = []

    for sequence, (node_id,) in enumerate(nodes, start=1):
        if node_id in INITIAL_CAPACITY:
            max_lines, used_lines, max_units, used_units = (
                INITIAL_CAPACITY[node_id]
            )
        else:
            max_lines = 80
            used_lines = 0
            max_units = 400
            used_units = 0

        records.append(
            (
                f"CAP-{sequence:06d}",
                node_id,
                CAPACITY_DATE,
                max_lines,
                used_lines,
                max_units,
                used_units,
            )
        )

    return records


def seed_capacity():
    with sqlite3.connect(DATABASE_FILE) as connection:
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
            ORDER BY n.node_id
            """
        ).fetchall()

    print(f"Warehouse capacity records found: {len(rows)}")

    for row in rows:
        print(row)


if __name__ == "__main__":
    seed_capacity()

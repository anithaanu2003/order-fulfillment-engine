
from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_FILE = PROJECT_ROOT / "data" / "fulfillment.db"


def seed_inventory():
    inventory_records = [
        ("INV-000001", "FUL-2026-000001", "SKU-000001", 10, 2),
        ("INV-000002", "FUL-2026-000001", "SKU-000002", 50, 5),
        ("INV-000003", "FUL-2026-000001", "SKU-000003", 30, 3),
        ("INV-000004", "FUL-2026-000001", "SKU-000004", 8, 1),
        ("INV-000005", "FUL-2026-000001", "SKU-000005", 40, 4),

        ("INV-000006", "FUL-2026-000002", "SKU-000001", 5, 1),
        ("INV-000007", "FUL-2026-000002", "SKU-000002", 25, 2),
        ("INV-000008", "FUL-2026-000002", "SKU-000003", 20, 2),
        ("INV-000009", "FUL-2026-000002", "SKU-000004", 12, 2),
        ("INV-000010", "FUL-2026-000002", "SKU-000005", 15, 1),

        ("INV-000011", "FUL-2026-000003", "SKU-000001", 3, 0),
        ("INV-000012", "FUL-2026-000003", "SKU-000002", 35, 3),
        ("INV-000013", "FUL-2026-000003", "SKU-000003", 15, 1),
        ("INV-000014", "FUL-2026-000003", "SKU-000004", 6, 0),
        ("INV-000015", "FUL-2026-000003", "SKU-000005", 20, 2),
    ]

    with sqlite3.connect(DATABASE_FILE) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        connection.executemany(
            """
            INSERT OR IGNORE INTO inventory (
                inventory_id,
                node_id,
                sku_id,
                available_quantity,
                reserved_quantity,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (*record, "2026-10-26T12:00:00")
                for record in inventory_records
            ],
        )

        rows = connection.execute(
            """
            SELECT
                n.node_name,
                s.sku_name,
                i.available_quantity,
                i.reserved_quantity,
                i.available_quantity - i.reserved_quantity
                    AS unreserved_quantity
            FROM inventory AS i
            JOIN fulfillment_nodes AS n
                ON i.node_id = n.node_id
            JOIN skus AS s
                ON i.sku_id = s.sku_id
            ORDER BY n.node_name, s.sku_name
            """
        ).fetchall()

    print(f"Inventory records found: {len(rows)}")
    print("\nWarehouse inventory:")

    for row in rows:
        print(row)


if __name__ == "__main__":
    seed_inventory()

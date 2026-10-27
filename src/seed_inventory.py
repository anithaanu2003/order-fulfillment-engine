
from pathlib import Path
import random
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_FILE = PROJECT_ROOT / "data" / "fulfillment.db"

SEED = 20261022
STOCK_TIMESTAMP = "2026-10-26T12:00:00"

INITIAL_STOCK = [
    (10, 2), (50, 5), (30, 3), (8, 1), (40, 4),
    (5, 1), (25, 2), (20, 2), (12, 2), (15, 1),
    (3, 0), (35, 3), (15, 1), (6, 0), (20, 2),
]


def generate_inventory_records(nodes, skus):
    rng = random.Random(SEED)
    inventory_records = []
    sequence = 1

    for node_index, (node_id,) in enumerate(nodes):
        for sku_index, (sku_id,) in enumerate(skus):
            if node_index < 3:
                available, reserved = INITIAL_STOCK[
                    node_index * len(skus) + sku_index
                ]
            else:
                available = rng.randint(10, 100)
                reserved = rng.randint(0, min(available // 4, 10))

            inventory_records.append(
                (
                    f"INV-{sequence:06d}",
                    node_id,
                    sku_id,
                    available,
                    reserved,
                    STOCK_TIMESTAMP,
                )
            )
            sequence += 1

    return inventory_records


def seed_inventory():
    with sqlite3.connect(DATABASE_FILE) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        nodes = connection.execute(
            "SELECT node_id FROM fulfillment_nodes ORDER BY node_id"
        ).fetchall()

        skus = connection.execute(
            "SELECT sku_id FROM skus ORDER BY sku_id"
        ).fetchall()

        if len(nodes) != 20:
            raise ValueError(
                f"Expected 20 fulfillment nodes, found {len(nodes)}."
            )

        if not skus:
            raise ValueError("No SKUs found. Seed master data first.")

        inventory_records = generate_inventory_records(nodes, skus)

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
            inventory_records,
        )

        total = connection.execute(
            "SELECT COUNT(*) FROM inventory"
        ).fetchone()[0]

        node_count = connection.execute(
            "SELECT COUNT(DISTINCT node_id) FROM inventory"
        ).fetchone()[0]

        print(f"Inventory records in database: {total}")
        print(f"Warehouses represented: {node_count}")
        print(f"Records generated this run: {len(inventory_records)}")


if __name__ == "__main__":
    seed_inventory()


from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_FILE = PROJECT_ROOT / "data" / "fulfillment.db"


def seed_master_data():
    with sqlite3.connect(DATABASE_FILE) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        # Sample products
        connection.executemany(
            """
            INSERT OR IGNORE INTO skus
                (sku_id, sku_name, category, unit_weight_kg)
            VALUES (?, ?, ?, ?)
            """,
            [
                ("SKU-000001", "Laptop", "Electronics", 1.8),
                ("SKU-000002", "Wireless Mouse", "Accessories", 0.15),
                ("SKU-000003", "Keyboard", "Accessories", 0.7),
                ("SKU-000004", "Monitor", "Electronics", 4.5),
                ("SKU-000005", "Headphones", "Audio", 0.3),
            ],
        )

        # Sample fulfillment nodes
        connection.executemany(
            """
            INSERT OR IGNORE INTO fulfillment_nodes
                (node_id, node_name, city, service_zone)
            VALUES (?, ?, ?, ?)
            """,
            [
                ("FUL-2026-000001", "Hyderabad Warehouse", "Hyderabad", "SOUTH"),
                ("FUL-2026-000002", "Bengaluru Warehouse", "Bengaluru", "SOUTH"),
                ("FUL-2026-000003", "Chennai Warehouse", "Chennai", "SOUTH"),
            ],
        )

        # Sample carriers
        connection.executemany(
            """
            INSERT OR IGNORE INTO carriers
                (carrier_id, carrier_name)
            VALUES (?, ?)
            """,
            [
                ("CAR-000001", "FastShip"),
                ("CAR-000002", "Reliable Express"),
                ("CAR-000003", "National Parcel"),
            ],
        )

        print("Master data inserted successfully.")

        # Verify row counts
        for table in ("skus", "fulfillment_nodes", "carriers"):
            count = connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            print(f"{table}: {count} records")


if __name__ == "__main__":
    seed_master_data()

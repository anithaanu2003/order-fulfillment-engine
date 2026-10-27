
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

        # Fulfillment nodes
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
                ("FUL-2026-000004", "Mumbai Warehouse", "Mumbai", "WEST"),
                ("FUL-2026-000005", "Pune Warehouse", "Pune", "WEST"),
                ("FUL-2026-000006", "Ahmedabad Warehouse", "Ahmedabad", "WEST"),
                ("FUL-2026-000007", "Delhi Warehouse", "Delhi", "NORTH"),
                ("FUL-2026-000008", "Jaipur Warehouse", "Jaipur", "NORTH"),
                ("FUL-2026-000009", "Lucknow Warehouse", "Lucknow", "NORTH"),
                ("FUL-2026-000010", "Kolkata Warehouse", "Kolkata", "EAST"),
                ("FUL-2026-000011", "Bhubaneswar Warehouse", "Bhubaneswar", "EAST"),
                ("FUL-2026-000012", "Patna Warehouse", "Patna", "EAST"),
                ("FUL-2026-000013", "Kochi Warehouse", "Kochi", "SOUTH"),
                ("FUL-2026-000014", "Coimbatore Warehouse", "Coimbatore", "SOUTH"),
                ("FUL-2026-000015", "Visakhapatnam Warehouse", "Visakhapatnam", "SOUTH"),
                ("FUL-2026-000016", "Indore Warehouse", "Indore", "CENTRAL"),
                ("FUL-2026-000017", "Bhopal Warehouse", "Bhopal", "CENTRAL"),
                ("FUL-2026-000018", "Nagpur Warehouse", "Nagpur", "CENTRAL"),
                ("FUL-2026-000019", "Guwahati Warehouse", "Guwahati", "NORTHEAST"),
                ("FUL-2026-000020", "Dehradun Warehouse", "Dehradun", "NORTH"),
            ],
        )
    
        # Carriers
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
                ("CAR-000004", "BlueDart"),
                ("CAR-000005", "Delhivery"),
                ("CAR-000006", "DTDC"),
                ("CAR-000007", "Ecom Express"),
                ("CAR-000008", "Shadowfax"),
                ("CAR-000009", "XpressBees"),
                ("CAR-000010", "India Post Logistics"),
            ],
        )

        # Verify row counts
        for table in ("skus", "fulfillment_nodes", "carriers"):
            count = connection.execute(
                f"SELECT COUNT(*) FROM {table}"
            ).fetchone()[0]
            print(f"{table}: {count} records")


if __name__ == "__main__":
    seed_master_data()

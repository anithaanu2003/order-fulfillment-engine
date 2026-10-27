
import sqlite3
from src.init_db import DATABASE_FILE

tables = [
    "skus",
    "fulfillment_nodes",
    "carriers",
    "inventory",
    "warehouse_capacity",
    "service_levels",
    "carrier_service_zones",
    "orders",
    "order_lines",
]

with sqlite3.connect(DATABASE_FILE) as connection:
    for table in tables:
        count = connection.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]
        print(f"{table}: {count}")

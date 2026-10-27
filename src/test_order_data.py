
from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_FILE = PROJECT_ROOT / "data" / "fulfillment.db"


def insert_sample_order():
    with sqlite3.connect(DATABASE_FILE) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        # Create one customer order.
        connection.execute(
            """
            INSERT INTO orders (
                order_id,
                order_timestamp,
                destination_city,
                destination_zone,
                order_status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "ORD-2026-000001",
                "2026-10-26T10:30:00",
                "Hyderabad",
                "SOUTH",
                "CREATED",
                "2026-10-26T10:30:00",
            ),
        )

        # Add two products to this order.
        connection.executemany(
            """
            INSERT INTO order_lines (
                order_line_id,
                order_id,
                sku_id,
                quantity,
                unit_price
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                (
                    "LINE-000001",
                    "ORD-2026-000001",
                    "SKU-000001",
                    1,
                    55000.00,
                ),
                (
                    "LINE-000002",
                    "ORD-2026-000001",
                    "SKU-000002",
                    2,
                    750.00,
                ),
            ],
        )

        print("Sample order inserted successfully!")

        # Retrieve the order and its product lines.
        rows = connection.execute(
            """
            SELECT
                o.order_id,
                o.destination_city,
                ol.order_line_id,
                s.sku_name,
                ol.quantity,
                ol.unit_price
            FROM orders AS o
            JOIN order_lines AS ol
                ON o.order_id = ol.order_id
            JOIN skus AS s
                ON ol.sku_id = s.sku_id
            WHERE o.order_id = ?
            ORDER BY ol.order_line_id
            """,
            ("ORD-2026-000001",),
        ).fetchall()

        print("\nOrder details:")

        for row in rows:
            print(row)

        print(f"\nNumber of order lines: {len(rows)}")

        # Test foreign-key enforcement.
        try:
            connection.execute(
                """
                INSERT INTO order_lines (
                    order_line_id,
                    order_id,
                    sku_id,
                    quantity,
                    unit_price
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "LINE-INVALID",
                    "ORD-2026-000001",
                    "SKU-DOES-NOT-EXIST",
                    1,
                    100.00,
                ),
            )

            raise AssertionError(
                "Invalid SKU was unexpectedly accepted."
            )

        except sqlite3.IntegrityError:
            print("\nPASS: Invalid SKU was rejected.")

        print("\nOrder data validation completed.")


if __name__ == "__main__":
    insert_sample_order()

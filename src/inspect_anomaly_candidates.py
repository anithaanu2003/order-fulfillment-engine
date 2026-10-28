
import sqlite3
from pathlib import Path

DATABASE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "fulfillment.db"
)


def main():
    connection = sqlite3.connect(
        DATABASE.as_uri() + "?mode=ro",
        uri=True,
    )
    connection.row_factory = sqlite3.Row

    checks = {
        "Promise before order": """
            SELECT COUNT(*)
            FROM delivery_promises p
            JOIN orders o ON o.order_id = p.order_id
            WHERE p.promise_created_at < o.order_timestamp
               OR p.promised_delivery_start < o.order_timestamp
        """,
        "Allocation exceeds inventory": """
            SELECT COUNT(*)
            FROM shipment_lines sl
            JOIN shipments s ON s.shipment_id = sl.shipment_id
            JOIN order_lines ol ON ol.order_line_id = sl.order_line_id
            JOIN inventory i
              ON i.node_id = s.node_id
             AND i.sku_id = ol.sku_id
            WHERE sl.quantity > i.available_quantity
        """,
        "Carrier unsupported for destination zone": """
            SELECT COUNT(*)
            FROM shipments s
            JOIN orders o ON o.order_id = s.order_id
            WHERE NOT EXISTS (
                SELECT 1
                FROM carrier_service_zones z
                WHERE z.carrier_id = s.carrier_id
                  AND z.service_level_id = s.service_level_id
                  AND z.service_zone = o.destination_zone
                  AND z.is_active = 1
            )
        """,
        "Delivered before dispatch": """
            SELECT COUNT(*)
            FROM shipments
            WHERE delivered_at IS NOT NULL
              AND dispatched_at IS NOT NULL
              AND delivered_at < dispatched_at
        """,
        "Split-shipment order quantity mismatch": """
            WITH ordered AS (
                SELECT order_id, order_line_id, quantity
                FROM order_lines
            ),
            shipped AS (
                SELECT
                    s.order_id,
                    sl.order_line_id,
                    SUM(sl.quantity) AS shipped_quantity
                FROM shipments s
                JOIN shipment_lines sl
                  ON sl.shipment_id = s.shipment_id
                GROUP BY s.order_id, sl.order_line_id
            )
            SELECT COUNT(*)
            FROM ordered o
            JOIN shipped s ON s.order_line_id = o.order_line_id
            WHERE s.shipped_quantity > o.quantity
        """,
    }

    try:
        print("Anomaly candidate inspection (read-only)")
        print("-" * 48)

        for label, query in checks.items():
            count = connection.execute(query).fetchone()[0]
            print(f"{label}: {count}")

        split_orders = connection.execute("""
            SELECT COUNT(*)
            FROM (
                SELECT order_id
                FROM shipments
                GROUP BY order_id
                HAVING COUNT(*) > 1
            )
        """).fetchone()[0]

        print(f"Orders with multiple shipments: {split_orders}")

    finally:
        connection.close()


if __name__ == "__main__":
    main()

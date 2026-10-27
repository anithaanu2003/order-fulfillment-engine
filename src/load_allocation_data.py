
import sqlite3

from .init_db import DATABASE_FILE


def load_inventory_records():
    """Load inventory records in the format used by the allocation engine."""
    with sqlite3.connect(DATABASE_FILE) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT
                node_id,
                sku_id,
                available_quantity,
                reserved_quantity
            FROM inventory
            ORDER BY node_id, sku_id
            """
        ).fetchall()

    return [dict(row) for row in rows]


def load_capacity_records():
    """Load warehouse capacity records for the current capacity date."""
    with sqlite3.connect(DATABASE_FILE) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT
                node_id,
                max_order_lines,
                used_order_lines,
                max_units,
                used_units
            FROM warehouse_capacity
            WHERE capacity_date = (
                SELECT MAX(capacity_date)
                FROM warehouse_capacity
            )
            ORDER BY node_id
            """
        ).fetchall()

    return [dict(row) for row in rows]


def load_orders_with_lines():
    """Load orders and group their order lines by order ID."""
    with sqlite3.connect(DATABASE_FILE) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT
                o.order_id,
                o.order_timestamp,
                o.destination_city,
                o.destination_zone,
                o.order_status,
                ol.order_line_id,
                ol.sku_id,
                ol.quantity,
                ol.unit_price
            FROM orders AS o
            INNER JOIN order_lines AS ol
                ON o.order_id = ol.order_id
            WHERE o.order_status = 'CREATED'
            ORDER BY o.order_id, ol.order_line_id
            """
        ).fetchall()

    orders = {}

    for row in rows:
        record = dict(row)
        order_id = record["order_id"]

        if order_id not in orders:
            orders[order_id] = {
                "order_id": order_id,
                "order_timestamp": record["order_timestamp"],
                "destination_city": record["destination_city"],
                "destination_zone": record["destination_zone"],
                "order_status": record["order_status"],
                "order_lines": [],
            }

        orders[order_id]["order_lines"].append({
            "order_line_id": record["order_line_id"],
            "sku_id": record["sku_id"],
            "quantity": record["quantity"],
            "unit_price": record["unit_price"],
        })

    return list(orders.values())



import sqlite3
from pathlib import Path

from .init_db import DATABASE_FILE

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def resolve_database_path(database_file=None):
    target = Path(database_file) if database_file is not None else DATABASE_FILE

    if not target.is_absolute():
        target = PROJECT_ROOT / target

    if not target.exists():
        raise FileNotFoundError(f"Database does not exist: {target}")

    return target


def load_inventory_records(database_file=None):
    """Load inventory records for the selected database."""
    target = resolve_database_path(database_file)

    with sqlite3.connect(target) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT node_id, sku_id, available_quantity, reserved_quantity
            FROM inventory
            ORDER BY node_id, sku_id
            """
        ).fetchall()

    return [dict(row) for row in rows]


def load_capacity_records(capacity_date=None, database_file=None):
    """Load capacity records for a specified date and database."""
    target = resolve_database_path(database_file)

    if capacity_date is None:
        capacity_date = "2026-10-26"

    with sqlite3.connect(target) as connection:
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
            WHERE capacity_date = ?
            ORDER BY node_id
            """,
            (capacity_date,),
        ).fetchall()

    return [dict(row) for row in rows]


def load_orders_with_lines(database_file=None):
    """Load CREATED orders and group their lines by order ID."""
    target = resolve_database_path(database_file)

    with sqlite3.connect(target) as connection:
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

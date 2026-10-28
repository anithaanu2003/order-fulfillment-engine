
import sqlite3
from pathlib import Path

from . import init_db
from .id_generator import (
    generate_shipment_id,
    generate_promise_id,
    generate_tracking_event_id,
)
from .select_carrier_service import select_carrier_service
from .calculate_delivery_promise import calculate_delivery_dates_for_carrier

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def resolve_database_path(database_file=None):
    target = (
        Path(database_file)
        if database_file is not None
        else init_db.DATABASE_FILE
    )

    if not target.is_absolute():
        target = PROJECT_ROOT / target

    if not target.exists():
        raise FileNotFoundError(f"Database does not exist: {target}")

    return target


def validate_allocations(order, allocations):
    """Check that allocations match the order's original lines."""
    if not isinstance(allocations, list) or not allocations:
        return False

    try:
        expected_lines = {
            line["order_line_id"]: (line["sku_id"], line["quantity"])
            for line in order["order_lines"]
        }
    except (KeyError, TypeError):
        return False

    actual_lines = {}

    for allocation in allocations:
        if not isinstance(allocation, dict):
            return False

        required_fields = {
            "order_line_id", "sku_id", "quantity", "node_id"
        }

        if not required_fields.issubset(allocation):
            return False

        line_id = allocation["order_line_id"]
        quantity = allocation["quantity"]

        if line_id in actual_lines:
            return False

        if not isinstance(quantity, int) or isinstance(quantity, bool):
            return False

        if quantity <= 0 or not allocation["node_id"]:
            return False

        actual_lines[line_id] = (allocation["sku_id"], quantity)

    return actual_lines == expected_lines


def persist_order_allocation(order, allocations, database_file=None):
    """
    Persist an order allocation atomically in the selected database.

    Returns False for invalid allocations, ineligible orders, or
    unavailable carrier services. Database changes are atomic.
    """
    if not validate_allocations(order, allocations):
        return False

    target = resolve_database_path(database_file)
    order_id = order["order_id"]
    order_timestamp = order["order_timestamp"]
    destination_zone = order["destination_zone"]

    with sqlite3.connect(target) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        try:
            current_status = connection.execute(
                "SELECT order_status FROM orders WHERE order_id = ?",
                (order_id,),
            ).fetchone()

            if current_status is None or current_status[0] != "CREATED":
                return False

            carrier_service = select_carrier_service(destination_zone, target)

            if carrier_service is None:
                return False

            delivery_dates = calculate_delivery_dates_for_carrier(
                order_timestamp=order_timestamp,
                transit_days=carrier_service["transit_days"],
                carrier_id=carrier_service["carrier_id"],
                service_zone=destination_zone,
                database_file=target,
            )
            capacity_date = delivery_dates["dispatch_date"]

            grouped = {}
            for allocation in allocations:
                grouped.setdefault(allocation["node_id"], []).append(
                    allocation
                )

            for node_id in grouped:
                capacity_exists = connection.execute(
                    """
                    SELECT 1 FROM warehouse_capacity
                    WHERE node_id = ? AND capacity_date = ?
                    """,
                    (node_id, capacity_date),
                ).fetchone()

                if capacity_exists is None:
                    raise ValueError(
                        "No warehouse capacity record for "
                        f"{node_id} on {capacity_date}"
                    )

            next_shipment_number = connection.execute(
                """
                SELECT COALESCE(
                    MAX(CAST(SUBSTR(shipment_id, 10) AS INTEGER)), 0
                ) + 1
                FROM shipments
                WHERE shipment_id LIKE 'SHP-2026-%'
                """
            ).fetchone()[0]

            next_line_number = connection.execute(
                """
                SELECT COALESCE(
                    MAX(CAST(SUBSTR(shipment_line_id, 7) AS INTEGER)), 0
                ) + 1
                FROM shipment_lines
                WHERE shipment_line_id LIKE 'SLINE-%'
                """
            ).fetchone()[0]

            now = order_timestamp
            shipment_number = next_shipment_number
            line_number = next_line_number

            for node_id, node_allocations in grouped.items():
                shipment_id = generate_shipment_id(shipment_number)
                shipment_number += 1

                connection.execute(
                    """
                    INSERT INTO shipments (
                        shipment_id, order_id, node_id, carrier_id,
                        service_level_id, shipment_status, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, 'CREATED', ?)
                    """,
                    (
                        shipment_id,
                        order_id,
                        node_id,
                        carrier_service["carrier_id"],
                        carrier_service["service_level_id"],
                        now,
                    ),
                )

                connection.execute(
                    """
                    INSERT INTO tracking_events (
                        tracking_event_id, shipment_id, event_sequence,
                        event_type, event_timestamp, event_location,
                        event_notes
                    )
                    VALUES (?, ?, 1, 'CREATED', ?, ?, ?)
                    """,
                    (
                        generate_tracking_event_id(shipment_id, 1),
                        shipment_id,
                        now,
                        node_id,
                        "Shipment created during order allocation",
                    ),
                )

                for allocation in node_allocations:
                    connection.execute(
                        """
                        INSERT INTO shipment_lines (
                            shipment_line_id, shipment_id,
                            order_line_id, quantity
                        )
                        VALUES (?, ?, ?, ?)
                        """,
                        (
                            f"SLINE-{line_number:06d}",
                            shipment_id,
                            allocation["order_line_id"],
                            allocation["quantity"],
                        ),
                    )
                    line_number += 1

            promise_id = generate_promise_id(order_id, 1)

            connection.execute(
                """
                INSERT INTO delivery_promises (
                    promise_id, order_id, promise_version,
                    promised_delivery_start, promised_delivery_end,
                    promise_created_at, promise_status
                )
                VALUES (?, ?, 1, ?, ?, ?, 'ACTIVE')
                """,
                (
                    promise_id,
                    order_id,
                    delivery_dates["promised_delivery_start"],
                    delivery_dates["promised_delivery_end"],
                    now,
                ),
            )

            cursor = connection.execute(
                """
                UPDATE orders SET order_status = 'ALLOCATED'
                WHERE order_id = ? AND order_status = 'CREATED'
                """,
                (order_id,),
            )

            if cursor.rowcount != 1:
                raise ValueError(
                    f"Order {order_id} is no longer eligible for allocation"
                )

            for allocation in allocations:
                cursor = connection.execute(
                    """
                    UPDATE inventory
                    SET reserved_quantity = reserved_quantity + ?,
                        updated_at = ?
                    WHERE node_id = ?
                      AND sku_id = ?
                      AND available_quantity - reserved_quantity >= ?
                    """,
                    (
                        allocation["quantity"],
                        now,
                        allocation["node_id"],
                        allocation["sku_id"],
                        allocation["quantity"],
                    ),
                )

                if cursor.rowcount != 1:
                    raise ValueError(
                        "Insufficient inventory for "
                        f"{allocation['sku_id']} at "
                        f"{allocation['node_id']}"
                    )

            for node_id, node_allocations in grouped.items():
                requested_lines = len(node_allocations)
                requested_units = sum(
                    allocation["quantity"]
                    for allocation in node_allocations
                )

                cursor = connection.execute(
                    """
                    UPDATE warehouse_capacity
                    SET used_order_lines = used_order_lines + ?,
                        used_units = used_units + ?
                    WHERE node_id = ?
                      AND capacity_date = ?
                      AND max_order_lines - used_order_lines >= ?
                      AND max_units - used_units >= ?
                    """,
                    (
                        requested_lines,
                        requested_units,
                        node_id,
                        capacity_date,
                        requested_lines,
                        requested_units,
                    ),
                )

                if cursor.rowcount != 1:
                    raise ValueError(
                        "Insufficient warehouse capacity at "
                        f"{node_id} on {capacity_date}"
                    )

            connection.commit()
            return True

        except Exception:
            connection.rollback()
            raise

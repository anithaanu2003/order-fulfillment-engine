
import sqlite3
from pathlib import Path
from datetime import datetime

from . import init_db
from .id_generator import generate_tracking_event_id


ALLOWED_EVENT_TYPES = {
    "CREATED",
    "ALLOCATED",
    "DISPATCHED",
    "IN_TRANSIT",
    "OUT_FOR_DELIVERY",
    "DELIVERED",
    "EXCEPTION",
    "CANCELLED",
}


ALLOWED_TRANSITIONS = {
    "CREATED": {"ALLOCATED", "DISPATCHED", "EXCEPTION", "CANCELLED"},
    "ALLOCATED": {"DISPATCHED", "EXCEPTION", "CANCELLED"},
    "DISPATCHED": {"IN_TRANSIT", "OUT_FOR_DELIVERY", "DELIVERED", "EXCEPTION"},
    "IN_TRANSIT": {"OUT_FOR_DELIVERY", "DELIVERED", "EXCEPTION"},
    "OUT_FOR_DELIVERY": {"DELIVERED", "EXCEPTION"},
    "EXCEPTION": {"IN_TRANSIT", "DISPATCHED", "CANCELLED"},
    "DELIVERED": set(),
    "CANCELLED": set(),
}


def resolve_database_path(database_file=None):
    """Resolve an optional database path without changing the default."""
    target = (
        Path(database_file)
        if database_file is not None
        else init_db.DATABASE_FILE
    )

    if not target.is_absolute():
        target = init_db.PROJECT_ROOT / target

    return target


def record_tracking_event(
    shipment_id,
    event_type,
    event_timestamp,
    event_location=None,
    event_notes=None,
    database_file=None,
):
    """Append a validated tracking event and update its shipment state.

    When database_file is supplied, every read and write uses that database.
    If any validation or database operation fails, the transaction is rolled
    back, including shipment and parent-order status changes.
    """

    if event_type not in ALLOWED_EVENT_TYPES:
        raise ValueError("Invalid tracking event type.")

    if not isinstance(shipment_id, str) or not shipment_id.startswith("SHP-"):
        raise ValueError("Invalid shipment ID.")

    if not event_timestamp:
        raise ValueError("Event timestamp is required.")

    try:
        event_time = datetime.fromisoformat(event_timestamp)
    except (TypeError, ValueError):
        raise ValueError("Invalid event timestamp format.") from None

    target_database = resolve_database_path(database_file)

    with sqlite3.connect(target_database) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        shipment = connection.execute(
            """
            SELECT shipment_id, shipment_status, dispatched_at, order_id
            FROM shipments
            WHERE shipment_id = ?
            """,
            (shipment_id,),
        ).fetchone()

        if shipment is None:
            raise ValueError("Shipment does not exist.")

        current_status = shipment[1]
        dispatched_at = shipment[2]
        order_id = shipment[3]

        if event_type not in ALLOWED_TRANSITIONS[current_status]:
            raise ValueError(
                f"Invalid shipment transition: "
                f"{current_status} -> {event_type}"
            )

        if event_type == "DELIVERED":
            dispatched_event = connection.execute(
                """
                SELECT 1
                FROM tracking_events
                WHERE shipment_id = ?
                  AND event_type = 'DISPATCHED'
                LIMIT 1
                """,
                (shipment_id,),
            ).fetchone()

            if dispatched_event is None or not dispatched_at:
                raise ValueError(
                    "A shipment cannot be delivered before dispatch."
                )

            dispatch_time = datetime.fromisoformat(dispatched_at)

            if event_time.tzinfo != dispatch_time.tzinfo:
                raise ValueError(
                    "Dispatch and delivery timestamps must use "
                    "compatible timezone information."
                )

            if event_time < dispatch_time:
                raise ValueError(
                    "Delivery timestamp cannot be earlier than dispatch."
                )

        latest_event = connection.execute(
            """
            SELECT event_timestamp
            FROM tracking_events
            WHERE shipment_id = ?
            ORDER BY event_sequence DESC
            LIMIT 1
            """,
            (shipment_id,),
        ).fetchone()

        if latest_event is not None:
            latest_time = datetime.fromisoformat(latest_event[0])

            if event_time.tzinfo != latest_time.tzinfo:
                raise ValueError(
                    "Tracking event timestamps must use "
                    "compatible timezone information."
                )

            if event_time < latest_time:
                raise ValueError(
                    "Tracking event timestamp cannot be earlier "
                    "than the previous event."
                )

        next_sequence = connection.execute(
            """
            SELECT COALESCE(MAX(event_sequence), 0) + 1
            FROM tracking_events
            WHERE shipment_id = ?
            """,
            (shipment_id,),
        ).fetchone()[0]

        event_id = generate_tracking_event_id(
            shipment_id,
            next_sequence,
        )

        connection.execute(
            """
            INSERT INTO tracking_events (
                tracking_event_id,
                shipment_id,
                event_sequence,
                event_type,
                event_timestamp,
                event_location,
                event_notes
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                shipment_id,
                next_sequence,
                event_type,
                event_timestamp,
                event_location,
                event_notes,
            ),
        )

        if event_type == "DISPATCHED":
            connection.execute(
                """
                UPDATE shipments
                SET shipment_status = ?,
                    dispatched_at = ?
                WHERE shipment_id = ?
                """,
                (event_type, event_timestamp, shipment_id),
            )

        elif event_type == "DELIVERED":
            connection.execute(
                """
                UPDATE shipments
                SET shipment_status = ?,
                    delivered_at = ?
                WHERE shipment_id = ?
                """,
                (event_type, event_timestamp, shipment_id),
            )

        else:
            connection.execute(
                """
                UPDATE shipments
                SET shipment_status = ?
                WHERE shipment_id = ?
                """,
                (event_type, shipment_id),
            )

        if event_type == "DELIVERED":
            current_order = connection.execute(
                """
                SELECT order_status
                FROM orders
                WHERE order_id = ?
                """,
                (order_id,),
            ).fetchone()

            if current_order is None:
                raise ValueError("Parent order does not exist.")

            if current_order[0] in {"CANCELLED", "EXCEPTION"}:
                raise ValueError(
                    "Cannot update the status of a cancelled "
                    "or exception order through shipment delivery."
                )

            total_shipments, delivered_shipments = connection.execute(
                """
                SELECT
                    COUNT(*),
                    SUM(
                        CASE
                            WHEN shipment_status = 'DELIVERED' THEN 1
                            ELSE 0
                        END
                    )
                FROM shipments
                WHERE order_id = ?
                """,
                (order_id,),
            ).fetchone()

            if delivered_shipments == total_shipments:
                order_status = "DELIVERED"
            else:
                order_status = "PARTIALLY_DELIVERED"

            connection.execute(
                """
                UPDATE orders
                SET order_status = ?
                WHERE order_id = ?
                """,
                (order_status, order_id),
            )

        return event_id

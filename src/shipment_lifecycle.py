
import sqlite3
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


def record_tracking_event(
    shipment_id,
    event_type,
    event_timestamp,
    event_location=None,
    event_notes=None,
):
    """Append a tracking event and update the shipment's current state."""

    if event_type not in ALLOWED_EVENT_TYPES:
        raise ValueError("Invalid tracking event type.")

    if not isinstance(shipment_id, str) or not shipment_id.startswith("SHP-"):
        raise ValueError("Invalid shipment ID.")

    if not event_timestamp:
        raise ValueError("Event timestamp is required.")

    # Validate that the timestamp has a supported ISO format.
    try:
        event_time = datetime.fromisoformat(event_timestamp)
    except (TypeError, ValueError):
        raise ValueError("Invalid event timestamp format.") from None

    with sqlite3.connect(init_db.DATABASE_FILE) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        shipment = connection.execute(
            """
            SELECT shipment_id, shipment_status, dispatched_at
            FROM shipments
            WHERE shipment_id = ?
            """,
            (shipment_id,),
        ).fetchone()

        if shipment is None:
            raise ValueError("Shipment does not exist.")

        current_status = shipment[1]
        dispatched_at = shipment[2]

        if event_type not in ALLOWED_TRANSITIONS[current_status]:
            raise ValueError(
                f"Invalid shipment transition: "
                f"{current_status} -> {event_type}"
            )

        # A shipment cannot be delivered before it has been dispatched.
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

            # Compare actual timestamps, not just shipment statuses.
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

        # Prevent tracking event timestamps from going backwards.
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

    return event_id

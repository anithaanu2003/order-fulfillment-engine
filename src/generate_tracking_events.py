
import random
import sqlite3

from datetime import datetime, timedelta

from . import init_db
from .shipment_lifecycle import record_tracking_event


RANDOM_SEED = 20261022
TARGET_EVENT_COUNT = 100_000

EVENT_LOCATIONS = [
    "Fulfillment Center",
    "Carrier Hub",
    "Transit Facility",
    "Destination Hub",
    "Delivery Address",
]


SAFE_TRANSITIONS = {
    "CREATED": [
        ("DISPATCHED", "Shipment dispatched"),
    ],
    "ALLOCATED": [
        ("DISPATCHED", "Shipment dispatched"),
    ],
    "DISPATCHED": [
        ("IN_TRANSIT", "Shipment entered transit"),
    ],
    "IN_TRANSIT": [
        ("OUT_FOR_DELIVERY", "Shipment is out for delivery"),
    ],
    "OUT_FOR_DELIVERY": [
        ("DELIVERED", "Shipment delivered successfully"),
    ],
    "EXCEPTION": [
        ("IN_TRANSIT", "Shipment resumed transit after exception"),
        ("DISPATCHED", "Shipment resumed dispatch after exception"),
    ],
}



def resolve_database_path(database_file=None):
    """Resolve the requested database path."""
    target = (
        database_file
        if database_file is not None
        else init_db.DATABASE_FILE
    )

    from pathlib import Path

    target = Path(target)

    if not target.is_absolute():
        target = init_db.PROJECT_ROOT / target

    return target


def get_tracking_event_count(database_file=None):
    """Return the number of tracking events in the selected database."""
    target = resolve_database_path(database_file)

    with sqlite3.connect(target) as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM tracking_events"
        ).fetchone()[0]


def get_shipments_needing_events(database_file=None):
    """Load eligible shipments and their most recent event timestamps."""
    target = resolve_database_path(database_file)

    with sqlite3.connect(target) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT
                s.shipment_id,
                s.shipment_status,
                s.created_at,
                (
                    SELECT te.event_timestamp
                    FROM tracking_events AS te
                    WHERE te.shipment_id = s.shipment_id
                    ORDER BY te.event_sequence DESC
                    LIMIT 1
                ) AS latest_event_timestamp
            FROM shipments AS s
            WHERE s.shipment_status NOT IN ('DELIVERED', 'CANCELLED')
            ORDER BY s.shipment_id
            """
        ).fetchall()

    return [dict(row) for row in rows]


def next_event_timestamp(previous_timestamp, rng):
    """Generate a reproducible timestamp later than the previous event."""
    previous_time = datetime.fromisoformat(previous_timestamp)

    next_time = previous_time + timedelta(
        hours=rng.randint(2, 12)
    )

    return next_time.isoformat(timespec="seconds")


def append_event(
    shipment_id,
    event_type,
    timestamp,
    location,
    notes,
    database_file=None,
):
    """Append an event using the lifecycle validator and chosen database."""
    return record_tracking_event(
        shipment_id=shipment_id,
        event_type=event_type,
        event_timestamp=timestamp,
        event_location=location,
        event_notes=notes,
        database_file=database_file,
    )


def append_one_safe_event(shipment, rng, database_file=None):
    """Append at most one valid, non-delivery event for one shipment."""
    shipment_id = shipment["shipment_id"]
    status = shipment["shipment_status"]

    choices = SAFE_TRANSITIONS.get(status, [])

    if not choices:
        return False

    event_type, notes = rng.choice(choices)

    previous_timestamp = (
        shipment["latest_event_timestamp"]
        or shipment["created_at"]
    )

    timestamp = next_event_timestamp(previous_timestamp, rng)

    append_event(
        shipment_id=shipment_id,
        event_type=event_type,
        timestamp=timestamp,
        location=rng.choice(EVENT_LOCATIONS),
        notes=notes,
        database_file=database_file,
    )

    return True


def generate_tracking_events(
    target_count=TARGET_EVENT_COUNT,
    database_file=None,
):
    """Append at most one valid event per eligible shipment per run."""
    if (
        not isinstance(target_count, int)
        or isinstance(target_count, bool)
        or target_count < 0
    ):
        raise ValueError(
            "Target event count must be a non-negative integer."
        )

    rng = random.Random(RANDOM_SEED)

    initial_count = get_tracking_event_count(database_file)

    if initial_count >= target_count:
        print(f"Tracking events already meet target: {initial_count}")
        return initial_count

    shipments = get_shipments_needing_events(database_file)
    added = 0

    for shipment in shipments:
        if initial_count + added >= target_count:
            break

        try:
            if append_one_safe_event(
                shipment,
                rng,
                database_file=database_file,
            ):
                added += 1

        except (ValueError, sqlite3.IntegrityError) as error:
            print(f"Skipped {shipment['shipment_id']}: {error}")

    final_count = get_tracking_event_count(database_file)

    print(f"Database: {resolve_database_path(database_file)}")
    print(f"Initial tracking events: {initial_count:,}")
    print(f"Events appended: {final_count - initial_count:,}")
    print(f"Final tracking events: {final_count:,}")
    print(f"Requested target: {target_count:,}")

    if final_count < target_count:
        print(
            "Target not reached. This generator intentionally adds "
            "at most one event per eligible shipment per run. A valid "
            "large event dataset requires a larger shipment population "
            "and a documented lifecycle/outcome generation plan."
        )

    return final_count


if __name__ == "__main__":
    # Keep the standalone example small.
    # It uses the default database unless an explicit path is supplied
    # by calling generate_tracking_events() from another command.
    generate_tracking_events(target_count=50)

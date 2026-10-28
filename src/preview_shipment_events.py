
import argparse
import sqlite3
from datetime import date, datetime, time, timedelta
from pathlib import Path

from .calculate_delivery_promise import (
    calculate_delivery_dates_with_calendar,
)
from .load_calendar_data import (
    load_calendar_data,
    load_carrier_calendar,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = PROJECT_ROOT / "data" / "assessment_dataset.db"
EARLIEST_DISPATCH_TIME = time(9, 0)


def resolve_database_path(database_file):
    """Resolve the requested database path."""
    path = Path(database_file)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    return path.resolve()


def read_shipments(database_file):
    """Read shipments, their latest event, service, and node details."""
    connection = sqlite3.connect(
        f"{database_file.as_uri()}?mode=ro",
        uri=True,
    )
    connection.row_factory = sqlite3.Row

    try:
        return connection.execute(
            """
            SELECT
                s.shipment_id,
                s.order_id,
                s.node_id,
                s.carrier_id,
                s.service_level_id,
                s.shipment_status,
                s.created_at,
                s.dispatched_at,
                s.delivered_at,
                n.service_zone,
                sl.transit_days,
                p.promised_delivery_end,
                (
                    SELECT e.event_type
                    FROM tracking_events e
                    WHERE e.shipment_id = s.shipment_id
                    ORDER BY e.event_sequence DESC
                    LIMIT 1
                ) AS latest_event_type,
                (
                    SELECT e.event_timestamp
                    FROM tracking_events e
                    WHERE e.shipment_id = s.shipment_id
                    ORDER BY e.event_sequence DESC
                    LIMIT 1
                ) AS latest_event_timestamp
            FROM shipments s
            LEFT JOIN fulfillment_nodes n
                ON n.node_id = s.node_id
            LEFT JOIN service_levels sl
                ON sl.service_level_id = s.service_level_id
            LEFT JOIN delivery_promises p
                ON p.order_id = s.order_id
            WHERE s.shipment_status IN ('CREATED', 'EXCEPTION')
            ORDER BY s.shipment_id
            """
        ).fetchall()
    finally:
        connection.close()


def propose_dispatch(shipment, database_file):
    """Return a safe dispatch proposal, or a reason it cannot be proposed."""
    if shipment["shipment_status"] != "CREATED":
        return None, "Needs manual review; shipment is not in CREATED state"

    if not shipment["latest_event_timestamp"]:
        return None, "No existing tracking event"

    if shipment["latest_event_type"] not in {"CREATED", "ALLOCATED"}:
        return None, (
            f"Unexpected latest event: {shipment['latest_event_type']}"
        )

    if shipment["transit_days"] is None:
        return None, "Missing service-level transit days"

    created_at = datetime.fromisoformat(shipment["created_at"])
    latest_at = datetime.fromisoformat(
        shipment["latest_event_timestamp"]
    )

    if created_at.tzinfo != latest_at.tzinfo:
        return None, "Creation and latest-event timezone information differs"

    calendar_data = load_calendar_data(
        database_file=database_file,
        carrier_id=shipment["carrier_id"],
        service_zone=shipment["service_zone"],
        node_id=shipment["node_id"],
    )
    carrier_calendar = load_carrier_calendar(
        database_file=database_file,
        carrier_id=shipment["carrier_id"],
    )

    holidays = calendar_data["holidays"]

    # A shipment cannot be dispatched before its creation or latest event.
    earliest_date = max(created_at.date(), latest_at.date())
    calendar_dates = sorted(
        date.fromisoformat(day)
        for day in carrier_calendar
        if date.fromisoformat(day) >= earliest_date
    )

    for candidate_date in calendar_dates:
        key = candidate_date.isoformat()
        calendar_entry = carrier_calendar[key]

        if not calendar_entry["is_operating"]:
            continue

        cutoff_text = calendar_entry["cutoff_time"]
        if not cutoff_text:
            continue

        if (
            candidate_date.weekday() >= 5
            or candidate_date.isoformat() in holidays
        ):
            continue

        cutoff = time.fromisoformat(cutoff_text)
        candidate_time = EARLIEST_DISPATCH_TIME

        if candidate_date == created_at.date():
            candidate_time = max(
                candidate_time,
                created_at.time().replace(tzinfo=None),
            )

        if candidate_date == latest_at.date():
            # Strictly advance beyond the previous event, even when
            # that event occurred at the same clock time.
            after_latest = (
                latest_at + timedelta(minutes=1)
            ).time().replace(tzinfo=None)

            candidate_time = max(candidate_time, after_latest)

        if candidate_time > cutoff:
            continue

        candidate = datetime.combine(
            candidate_date,
            candidate_time,
            tzinfo=latest_at.tzinfo,
        )

        if candidate <= latest_at:
            continue

        try:
            promise_estimate = calculate_delivery_dates_with_calendar(
                order_timestamp=candidate.isoformat(),
                transit_days=shipment["transit_days"],
                holidays=holidays,
                carrier_calendar=carrier_calendar,
            )
        except (ValueError, TypeError) as error:
            return None, f"Promise estimate failed: {error}"

        promised_end = shipment["promised_delivery_end"]
        estimated_end = promise_estimate["promised_delivery_end"]

        return {
            "shipment_id": shipment["shipment_id"],
            "status": shipment["shipment_status"],
            "latest_event": shipment["latest_event_type"],
            "latest_event_timestamp": shipment["latest_event_timestamp"],
            "proposed_event": "DISPATCHED",
            "proposed_timestamp": candidate.isoformat(),
            "carrier_id": shipment["carrier_id"],
            "cutoff_time": cutoff_text,
            "estimated_delivery_end": estimated_end,
            "existing_promise_end": promised_end,
            "potentially_late": (
                bool(promised_end) and estimated_end > promised_end
            ),
        }, None

    return None, "No eligible operating date and cutoff found"


def main():
    parser = argparse.ArgumentParser(
        description="Preview safe dispatch events without modifying the DB."
    )
    parser.add_argument(
        "--database",
        default=str(DEFAULT_DATABASE),
        help="Database path (defaults to data/assessment_dataset.db)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of shipment proposals to print",
    )
    args = parser.parse_args()

    if args.limit < 1:
        parser.error("--limit must be at least 1")

    database_file = resolve_database_path(args.database)

    if not database_file.is_file():
        parser.error(f"Database not found: {database_file}")

    print("READ-ONLY DISPATCH PREVIEW")
    print(f"Database: {database_file}")
    print("No database changes will be made.\n")

    shipments = read_shipments(database_file)

    proposals = []
    skipped = []

    for shipment in shipments:
        proposal, reason = propose_dispatch(shipment, database_file)

        if proposal:
            proposals.append(proposal)
        else:
            skipped.append((shipment["shipment_id"], reason))

    print(f"Shipments reviewed: {len(shipments)}")
    print(f"Dispatch proposals: {len(proposals)}")
    print(f"Skipped for review: {len(skipped)}")
    print(
        "Potentially late against existing promise: "
        f"{sum(item['potentially_late'] for item in proposals)}"
    )

    print(f"\nFirst {min(args.limit, len(proposals))} proposals:")
    for item in proposals[:args.limit]:
        print(
            f"{item['shipment_id']} | "
            f"{item['proposed_timestamp']} | "
            f"estimated delivery {item['estimated_delivery_end']} | "
            f"existing promise {item['existing_promise_end']} | "
            f"potentially late: {item['potentially_late']}"
        )

    if skipped:
        print(f"\nFirst {min(args.limit, len(skipped))} skipped shipments:")
        for shipment_id, reason in skipped[:args.limit]:
            print(f"{shipment_id} | {reason}")


if __name__ == "__main__":
    main()

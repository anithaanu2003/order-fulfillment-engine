
from pathlib import Path
import random
import sqlite3
from contextlib import closing
from datetime import date, timedelta

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_FILE = PROJECT_ROOT / "data" / "fulfillment.db"

SEED = 20261022

START_DATE = date(2026, 10, 1)
END_DATE = date(2026, 12, 31)

# Fixed, synthetic holidays for deterministic dataset generation.
HOLIDAYS = [
    ("HOL-2026-001", date(2026, 10, 2), "Gandhi Jayanti", None),
    ("HOL-2026-002", date(2026, 10, 20), "Regional Festival Holiday", "SOUTH"),
    ("HOL-2026-003", date(2026, 11, 8), "Regional Festival Holiday", "NORTH"),
    ("HOL-2026-004", date(2026, 11, 14), "Children's Day Observance", None),
    ("HOL-2026-005", date(2026, 12, 25), "Christmas", None),
]


def date_range(start_date, end_date):
    """Yield each date from start_date through end_date, inclusive."""
    current = start_date

    while current <= end_date:
        yield current
        current += timedelta(days=1)


def generate_holiday_records(nodes):
    """Generate deterministic holiday records for the supplied nodes."""
    records = []

    for holiday_id, holiday_date, holiday_name, zone in HOLIDAYS:
        matching_nodes = [
            node_id
            for node_id, service_zone in nodes
            if zone is None or service_zone == zone
        ]

        if zone is None:
            # Represent a network-wide holiday once.
            records.append(
                (
                    holiday_id,
                    holiday_date.isoformat(),
                    holiday_name,
                    None,
                    None,
                    1,
                )
            )
        elif matching_nodes:
            # Create one record for each node in the affected zone.
            for node_id in matching_nodes:
                records.append(
                    (
                        f"{holiday_id}-{node_id}",
                        holiday_date.isoformat(),
                        holiday_name,
                        zone,
                        node_id,
                        1,
                    )
                )
        else:
            # Preserve a zone-level holiday if no node matches that zone.
            records.append(
                (
                    holiday_id,
                    holiday_date.isoformat(),
                    holiday_name,
                    zone,
                    None,
                    1,
                )
            )

    return records


def generate_carrier_calendar_records(carriers):
    """Generate deterministic daily operating calendars for each carrier."""
    rng = random.Random(SEED)
    records = []

    for (carrier_id,) in carriers:
        sequence = 1

        for current_date in date_range(START_DATE, END_DATE):
            weekday = current_date.weekday()

            # Carriers normally operate Monday through Saturday.
            is_operating = weekday != 6

            # Some carriers also operate on selected Sundays.
            if weekday == 6 and rng.random() < 0.15:
                is_operating = True

            cutoff_time = (
                "14:00"
                if carrier_id.endswith(("1", "5", "9"))
                else "17:00"
            )

            if not is_operating:
                cutoff_time = None

            records.append(
                (
                    f"CAL-{carrier_id}-{sequence:04d}",
                    carrier_id,
                    current_date.isoformat(),
                    int(is_operating),
                    cutoff_time,
                    "Synthetic deterministic carrier calendar",
                )
            )

            sequence += 1

    return records


def seed_calendars(database_file=None):
    """Seed calendars into an existing database without replacing records."""
    target_database = (
        Path(database_file)
        if database_file is not None
        else DATABASE_FILE
    )

    if not target_database.is_absolute():
        target_database = PROJECT_ROOT / target_database

    if not target_database.exists():
        raise FileNotFoundError(
            f"Database does not exist: {target_database}. "
            "Initialize the schema and seed master data in the test "
            "database first."
        )

    # closing() explicitly closes the SQLite connection.
    # The inner connection context commits or rolls back the transaction.
    with closing(sqlite3.connect(target_database)) as connection:
        with connection:
            connection.execute("PRAGMA foreign_keys = ON")

            tables = {
                row[0]
                for row in connection.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table'
                    """
                )
            }

            required_tables = {
                "fulfillment_nodes",
                "carriers",
                "holidays",
                "carrier_calendars",
            }

            missing = required_tables - tables
            if missing:
                raise RuntimeError(
                    "Missing required tables: "
                    + ", ".join(sorted(missing))
                )

            nodes = connection.execute(
                """
                SELECT node_id, service_zone
                FROM fulfillment_nodes
                ORDER BY node_id
                """
            ).fetchall()

            carriers = connection.execute(
                """
                SELECT carrier_id
                FROM carriers
                ORDER BY carrier_id
                """
            ).fetchall()

            if not nodes or not carriers:
                raise RuntimeError(
                    "Seed fulfillment nodes and carriers before calendars."
                )

            holiday_records = generate_holiday_records(nodes)
            calendar_records = generate_carrier_calendar_records(carriers)

            connection.executemany(
                """
                INSERT OR IGNORE INTO holidays (
                    holiday_id,
                    holiday_date,
                    holiday_name,
                    service_zone,
                    node_id,
                    is_active
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                holiday_records,
            )

            connection.executemany(
                """
                INSERT OR IGNORE INTO carrier_calendars (
                    carrier_calendar_id,
                    carrier_id,
                    calendar_date,
                    is_operating,
                    cutoff_time,
                    notes
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                calendar_records,
            )

            holiday_count = connection.execute(
                "SELECT COUNT(*) FROM holidays"
            ).fetchone()[0]

            calendar_count = connection.execute(
                "SELECT COUNT(*) FROM carrier_calendars"
            ).fetchone()[0]

    print(f"Database: {target_database}")
    print(f"Holiday records present: {holiday_count}")
    print(f"Carrier calendar records present: {calendar_count}")


if __name__ == "__main__":
    seed_calendars()

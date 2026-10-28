
import random
import sqlite3
from pathlib import Path

from . import init_db


RANDOM_SEED = 20261022
TARGET_SCAN_COUNT = 100

SCAN_LOCATIONS = [
    "Origin Fulfillment Center",
    "Carrier Processing Facility",
]

SCAN_TYPE = "LABEL_CREATED"


def resolve_database_path(database_file=None):
    """Resolve the explicitly supplied database path."""
    target = (
        Path(database_file)
        if database_file is not None
        else Path(init_db.DATABASE_FILE)
    )

    if not target.is_absolute():
        target = init_db.PROJECT_ROOT / target

    return target


def get_carrier_scan_count(database_file=None):
    """Return the total number of carrier scans."""
    target = resolve_database_path(database_file)

    with sqlite3.connect(target) as connection:
        return connection.execute(
            "SELECT COUNT(*) FROM carrier_scans"
        ).fetchone()[0]


def generate_carrier_scans(
    target_count=TARGET_SCAN_COUNT,
    database_file=None,
):
    """
    Generate reproducible LABEL_CREATED scans for CREATED shipments.

    Does not change shipment statuses or tracking events.
    """
    if (
        not isinstance(target_count, int)
        or isinstance(target_count, bool)
    ):
        raise ValueError("Target count must be an integer.")

    if target_count < 0:
        raise ValueError("Target count cannot be negative.")

    target = resolve_database_path(database_file)

    if not target.is_file():
        raise FileNotFoundError(
            f"Database does not exist: {target}"
        )

    rng = random.Random(RANDOM_SEED)

    with sqlite3.connect(target) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        # Verify that this database has the required tables.
        required_tables = {"shipments", "carriers", "carrier_scans"}
        existing_tables = {
            row[0]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            ).fetchall()
        }

        missing_tables = required_tables - existing_tables
        if missing_tables:
            raise RuntimeError(
                "Required tables are missing: "
                + ", ".join(sorted(missing_tables))
            )

        initial_count = connection.execute(
            "SELECT COUNT(*) FROM carrier_scans"
        ).fetchone()[0]

        if initial_count >= target_count:
            print(f"Database: {target}")
            print(f"Carrier scans already meet target: {initial_count}")
            return initial_count

        # Only CREATED shipments without a label scan are eligible.
        shipments = connection.execute(
            """
            SELECT
                s.shipment_id,
                s.carrier_id,
                s.created_at
            FROM shipments AS s
            WHERE s.shipment_status = 'CREATED'
              AND NOT EXISTS (
                  SELECT 1
                  FROM carrier_scans AS cs
                  WHERE cs.shipment_id = s.shipment_id
                    AND cs.scan_type = 'LABEL_CREATED'
              )
            ORDER BY s.shipment_id
            """
        ).fetchall()

        added = 0

        for shipment_id, carrier_id, created_at in shipments:
            if initial_count + added >= target_count:
                break

            sequence = connection.execute(
                """
                SELECT COALESCE(MAX(scan_sequence), 0) + 1
                FROM carrier_scans
                WHERE shipment_id = ?
                """,
                (shipment_id,),
            ).fetchone()[0]

            scan_id = f"CSN-{shipment_id}-{sequence:06d}"

            connection.execute(
                """
                INSERT INTO carrier_scans (
                    carrier_scan_id,
                    shipment_id,
                    scan_sequence,
                    carrier_id,
                    scan_type,
                    scan_timestamp,
                    scan_location,
                    scan_notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    scan_id,
                    shipment_id,
                    sequence,
                    carrier_id,
                    SCAN_TYPE,
                    created_at,
                    rng.choice(SCAN_LOCATIONS),
                    "Synthetic label-created scan; "
                    "shipment not yet dispatched",
                ),
            )

            added += 1

        final_count = initial_count + added

        print(f"Database: {target}")
        print(f"Initial carrier scans: {initial_count}")
        print(f"Carrier scans added: {added}")
        print(f"Final carrier scans: {final_count}")
        print(f"Requested target: {target_count}")

        if final_count < target_count:
            print(
                "Target not reached: more eligible CREATED "
                "shipments are needed."
            )

        return final_count


if __name__ == "__main__":
    # Standalone execution retains the default database.
    # For the assessment database, pass its path explicitly.
    generate_carrier_scans(target_count=10)

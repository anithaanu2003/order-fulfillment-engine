
import sqlite3
from pathlib import Path

from . import init_db

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


def get_eligible_carrier_services(destination_zone, database_file=None):
    """Return active carrier services supporting the destination zone."""
    target = resolve_database_path(database_file)

    with sqlite3.connect(target) as connection:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT
                c.carrier_id,
                c.carrier_name,
                sl.service_level_id,
                sl.service_name,
                sl.transit_days,
                sl.cutoff_time
            FROM carrier_service_zones AS csz
            JOIN carriers AS c
                ON c.carrier_id = csz.carrier_id
            JOIN service_levels AS sl
                ON sl.service_level_id = csz.service_level_id
            WHERE csz.service_zone = ?
              AND csz.is_active = 1
              AND c.is_active = 1
              AND sl.is_active = 1
            ORDER BY
                sl.transit_days ASC,
                c.carrier_name ASC
            """,
            (destination_zone,),
        ).fetchall()

    return [dict(row) for row in rows]


def select_carrier_service(destination_zone, database_file=None):
    """Choose the fastest eligible service, breaking ties by carrier name."""
    options = get_eligible_carrier_services(destination_zone, database_file)

    if not options:
        return None

    return options[0]


import sqlite3

from . import init_db


def get_eligible_carrier_services(destination_zone):
    """Return active carrier services that support the destination zone."""
    with sqlite3.connect(init_db.DATABASE_FILE) as connection:
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


def select_carrier_service(destination_zone):
    """Choose the fastest eligible service, breaking ties by carrier name."""
    options = get_eligible_carrier_services(destination_zone)

    if not options:
        return None

    return options[0]


import sqlite3
from pathlib import Path


DEFAULT_DATABASE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "fulfillment.db"
)


def load_calendar_data(
    database_file=None,
    carrier_id=None,
    service_zone=None,
    node_id=None,
):
    """
    Load active holidays and carrier operating dates without modifying the DB.

    Holiday filtering:
    - No filters: return all active holidays.
    - Service zone only: include global and matching-zone holidays.
    - Node only: include global and matching-node holidays.
    - Both: include global holidays and holidays matching both
      the requested zone and node, including zone-wide holidays.
    """
    db_path = Path(database_file) if database_file else DEFAULT_DATABASE

    connection = sqlite3.connect(
        f"{db_path.resolve().as_uri()}?mode=ro",
        uri=True,
    )

    try:
        connection.row_factory = sqlite3.Row

        tables = {
            row["name"]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                """
            )
        }

        required_tables = {"holidays", "carrier_calendars"}
        missing_tables = required_tables - tables

        if missing_tables:
            raise ValueError(
                f"Missing required calendar tables: {sorted(missing_tables)}"
            )

        holiday_sql = """
            SELECT DISTINCT holiday_date
            FROM holidays
            WHERE is_active = 1
        """
        holiday_params = []

        if service_zone is not None and node_id is not None:
            holiday_sql += """
                AND (
                    (service_zone IS NULL AND node_id IS NULL)
                    OR (
                        service_zone = ?
                        AND (node_id IS NULL OR node_id = ?)
                    )
                    OR (
                        node_id = ?
                        AND service_zone IS NULL
                    )
                )
            """
            holiday_params.extend(
                [service_zone, node_id, node_id]
            )

        elif service_zone is not None:
            holiday_sql += """
                AND (
                    (service_zone IS NULL AND node_id IS NULL)
                    OR service_zone = ?
                )
            """
            holiday_params.append(service_zone)

        elif node_id is not None:
            holiday_sql += """
                AND (
                    (service_zone IS NULL AND node_id IS NULL)
                    OR node_id = ?
                )
            """
            holiday_params.append(node_id)

        holiday_rows = connection.execute(
            holiday_sql,
            holiday_params,
        ).fetchall()

        operating_sql = """
            SELECT DISTINCT calendar_date
            FROM carrier_calendars
            WHERE is_operating = 1
        """
        operating_params = []

        if carrier_id is not None:
            operating_sql += " AND carrier_id = ?"
            operating_params.append(carrier_id)

        operating_rows = connection.execute(
            operating_sql,
            operating_params,
        ).fetchall()

        return {
            "holidays": {
                row["holiday_date"] for row in holiday_rows
            },
            "carrier_operating_days": {
                row["calendar_date"] for row in operating_rows
            },
        }

    finally:
        connection.close()


def load_carrier_calendar_entry(
    database_file=None,
    carrier_id=None,
    calendar_date=None,
):
    """Return one carrier's operating status and cutoff for a date."""
    if not carrier_id or not calendar_date:
        raise ValueError("carrier_id and calendar_date are required")

    db_path = Path(database_file) if database_file else DEFAULT_DATABASE

    connection = sqlite3.connect(
        f"{db_path.resolve().as_uri()}?mode=ro",
        uri=True,
    )

    try:
        connection.row_factory = sqlite3.Row

        row = connection.execute(
            """
            SELECT is_operating, cutoff_time
            FROM carrier_calendars
            WHERE carrier_id = ? AND calendar_date = ?
            """,
            (carrier_id, calendar_date),
        ).fetchone()

        if row is None:
            return None

        return {
            "is_operating": bool(row["is_operating"]),
            "cutoff_time": row["cutoff_time"],
        }
    finally:
        connection.close()


def load_carrier_calendar(database_file=None, carrier_id=None):
    """Load each date's operating status and cutoff for one carrier."""
    if not carrier_id:
        raise ValueError("carrier_id is required")

    db_path = Path(database_file) if database_file else DEFAULT_DATABASE

    connection = sqlite3.connect(
        f"{db_path.resolve().as_uri()}?mode=ro",
        uri=True,
    )

    try:
        connection.row_factory = sqlite3.Row

        rows = connection.execute(
            """
            SELECT calendar_date, is_operating, cutoff_time
            FROM carrier_calendars
            WHERE carrier_id = ?
            ORDER BY calendar_date
            """,
            (carrier_id,),
        ).fetchall()

        return {
            row["calendar_date"]: {
                "is_operating": bool(row["is_operating"]),
                "cutoff_time": row["cutoff_time"],
            }
            for row in rows
        }
    finally:
        connection.close()




if __name__ == "__main__":
    calendar_data = load_calendar_data()

    print(f"Active holiday dates: {len(calendar_data['holidays'])}")
    print(
        "Operating dates across carriers: "
        f"{len(calendar_data['carrier_operating_days'])}"
    )

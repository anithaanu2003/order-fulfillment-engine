
import sqlite3

from src.calculate_delivery_promise_from_db import (
    calculate_delivery_promise_from_db,
)


def test_delivery_promise_uses_database_calendar(tmp_path):
    database_file = tmp_path / "promise_test.db"
    connection = sqlite3.connect(database_file)

    try:
        connection.executescript(
            """
            CREATE TABLE holidays (
                holiday_id TEXT PRIMARY KEY,
                holiday_date TEXT NOT NULL,
                is_active INTEGER NOT NULL
            );

            CREATE TABLE carrier_calendars (
                carrier_calendar_id TEXT PRIMARY KEY,
                carrier_id TEXT NOT NULL,
                calendar_date TEXT NOT NULL,
                is_operating INTEGER NOT NULL
            );

            INSERT INTO holidays VALUES
                ('HOL-001', '2026-10-27', 1);

            INSERT INTO carrier_calendars VALUES
                ('CAL-001', 'CARRIER-1', '2026-10-26', 1),
                ('CAL-002', 'CARRIER-1', '2026-10-27', 1),
                ('CAL-003', 'CARRIER-1', '2026-10-28', 1),
                ('CAL-004', 'CARRIER-1', '2026-10-29', 1);
            """
        )
        connection.commit()
    finally:
        connection.close()

    result = calculate_delivery_promise_from_db(
        order_timestamp="2026-10-26T10:00:00",
        cutoff_time="17:00",
        transit_days=1,
        carrier_id="CARRIER-1",
        database_file=database_file,
    )

    assert result["dispatch_date"] == "2026-10-26"
    assert result["promised_delivery_start"] == "2026-10-28"
    assert result["promised_delivery_end"] == "2026-10-28"

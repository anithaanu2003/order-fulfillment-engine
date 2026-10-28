
import sqlite3

from src.load_calendar_data import load_calendar_data


def create_calendar_database(database_file):
    connection = sqlite3.connect(database_file)

    try:
        connection.executescript(
            """
            CREATE TABLE holidays (
                holiday_id TEXT PRIMARY KEY,
                holiday_date TEXT NOT NULL,
                holiday_name TEXT NOT NULL,
                service_zone TEXT,
                node_id TEXT,
                is_active INTEGER NOT NULL
            );

            CREATE TABLE carrier_calendars (
                carrier_calendar_id TEXT PRIMARY KEY,
                carrier_id TEXT NOT NULL,
                calendar_date TEXT NOT NULL,
                is_operating INTEGER NOT NULL
            );

            INSERT INTO holidays VALUES
                ('HOL-001', '2026-10-02', 'Global Holiday', NULL, NULL, 1),
                ('HOL-002', '2026-10-20', 'South Holiday', 'SOUTH', NULL, 1),
                ('HOL-003', '2026-11-08', 'North Holiday', 'NORTH', NULL, 1),
                ('HOL-004', '2026-10-21', 'Node Holiday', NULL, 'NODE-1', 1),
                ('HOL-005', '2026-11-01', 'Inactive Holiday', 'SOUTH', NULL, 0);

            INSERT INTO carrier_calendars VALUES
                ('CAL-001', 'CARRIER-1', '2026-10-21', 1),
                ('CAL-002', 'CARRIER-1', '2026-10-22', 1),
                ('CAL-003', 'CARRIER-1', '2026-10-23', 0),
                ('CAL-004', 'CARRIER-2', '2026-10-21', 1);
            """
        )
        connection.commit()
    finally:
        connection.close()


def test_load_calendar_data_reads_holidays_and_carrier_dates(tmp_path):
    database_file = tmp_path / "calendar_test.db"
    create_calendar_database(database_file)

    result = load_calendar_data(
        database_file=database_file,
        carrier_id="CARRIER-1",
    )

    assert result["holidays"] == {
        "2026-10-02",
        "2026-10-20",
        "2026-10-21",
        "2026-11-08",
    }

    assert result["carrier_operating_days"] == {
        "2026-10-21",
        "2026-10-22",
    }


def test_service_zone_filters_regional_holidays(tmp_path):
    database_file = tmp_path / "calendar_test.db"
    create_calendar_database(database_file)

    result = load_calendar_data(
        database_file=database_file,
        service_zone="SOUTH",
    )

    assert result["holidays"] == {
        "2026-10-02",
        "2026-10-20",
    }


def test_node_filter_includes_global_and_matching_node_holidays(tmp_path):
    database_file = tmp_path / "calendar_test.db"
    create_calendar_database(database_file)

    result = load_calendar_data(
        database_file=database_file,
        node_id="NODE-1",
    )

    assert result["holidays"] == {
        "2026-10-02",
        "2026-10-21",
    }
def test_service_zone_and_node_filters_apply_together(tmp_path):
    database_file = tmp_path / "calendar_test.db"
    create_calendar_database(database_file)

    result = load_calendar_data(
        database_file=database_file,
        service_zone="SOUTH",
        node_id="NODE-1",
    )

    assert result["holidays"] == {
        "2026-10-02",
        "2026-10-20",
        "2026-10-21",
    }


def test_holiday_with_both_zone_and_node_is_filtered_correctly(tmp_path):
    import sqlite3

    database_file = tmp_path / "calendar_test.db"
    create_calendar_database(database_file)

    with sqlite3.connect(database_file) as connection:
        connection.execute(
            """
            INSERT INTO holidays (
                holiday_id,
                holiday_date,
                holiday_name,
                service_zone,
                node_id,
                is_active
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "H-REALISTIC",
                "2026-10-22",
                "South Node Holiday",
                "SOUTH",
                "NODE-1",
                1,
            ),
        )

    south_result = load_calendar_data(
        database_file=database_file,
        service_zone="SOUTH",
    )
    node_result = load_calendar_data(
        database_file=database_file,
        node_id="NODE-1",
    )
    matching_result = load_calendar_data(
        database_file=database_file,
        service_zone="SOUTH",
        node_id="NODE-1",
    )
    wrong_node_result = load_calendar_data(
        database_file=database_file,
        service_zone="SOUTH",
        node_id="NODE-2",
    )

    assert "2026-10-22" in south_result["holidays"]
    assert "2026-10-22" in node_result["holidays"]
    assert "2026-10-22" in matching_result["holidays"]
    assert "2026-10-22" not in wrong_node_result["holidays"]

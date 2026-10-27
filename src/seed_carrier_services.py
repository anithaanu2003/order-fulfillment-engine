
from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_FILE = PROJECT_ROOT / "data" / "fulfillment.db"


def seed_carrier_services():
    service_records = [
        ("SVC-000001", "STANDARD", 3, "17:00", 1),
        ("SVC-000002", "EXPRESS", 1, "14:00", 1),
        ("SVC-000003", "ECONOMY", 5, "18:00", 1),
    ]

    route_records = [
        ("CSZ-000001", "CAR-000001", "SVC-000001", "SOUTH", 1),
        ("CSZ-000002", "CAR-000001", "SVC-000002", "SOUTH", 1),
        ("CSZ-000003", "CAR-000002", "SVC-000001", "SOUTH", 1),
        ("CSZ-000004", "CAR-000002", "SVC-000003", "SOUTH", 1),
        ("CSZ-000005", "CAR-000003", "SVC-000001", "SOUTH", 1),
        ("CSZ-000006", "CAR-000003", "SVC-000003", "SOUTH", 1),
    ]

    with sqlite3.connect(DATABASE_FILE) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        connection.executemany(
            """
            INSERT OR IGNORE INTO service_levels (
                service_level_id,
                service_name,
                transit_days,
                cutoff_time,
                is_active
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            service_records,
        )

        connection.executemany(
            """
            INSERT OR IGNORE INTO carrier_service_zones (
                carrier_service_zone_id,
                carrier_id,
                service_level_id,
                service_zone,
                is_active
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            route_records,
        )

        services = connection.execute(
            """
            SELECT service_level_id, service_name, transit_days, cutoff_time
            FROM service_levels
            ORDER BY service_level_id
            """
        ).fetchall()

        routes = connection.execute(
            """
            SELECT
                c.carrier_name,
                s.service_name,
                z.service_zone
            FROM carrier_service_zones AS z
            JOIN carriers AS c ON z.carrier_id = c.carrier_id
            JOIN service_levels AS s
                ON z.service_level_id = s.service_level_id
            ORDER BY c.carrier_name, s.service_name
            """
        ).fetchall()

    print(f"Delivery services found: {len(services)}")
    for service in services:
        print(service)

    print(f"\nCarrier routes found: {len(routes)}")
    for route in routes:
        print(route)


if __name__ == "__main__":
    seed_carrier_services()

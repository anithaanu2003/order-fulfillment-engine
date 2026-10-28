
from pathlib import Path
import sqlite3

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_FILE = PROJECT_ROOT / "data" / "fulfillment.db"

ZONES = ("SOUTH", "WEST", "NORTH", "EAST", "CENTRAL", "NORTHEAST")


def seed_carrier_services(database_file=None):
    target_database = (
        Path(database_file)
        if database_file is not None
        else DATABASE_FILE
    )

    if not target_database.is_absolute():
        target_database = PROJECT_ROOT / target_database

    if not target_database.is_file():
        raise FileNotFoundError(
            f"Database not found: {target_database}. "
            "Initialize the database and seed master data first."
        )

    service_records = [
        ("SVC-000001", "STANDARD", 3, "17:00", 1),
        ("SVC-000002", "EXPRESS", 1, "14:00", 1),
        ("SVC-000003", "ECONOMY", 5, "18:00", 1),
    ]

    with sqlite3.connect(target_database) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        carriers = connection.execute(
            "SELECT carrier_id FROM carriers ORDER BY carrier_id"
        ).fetchall()

        if len(carriers) != 10:
            raise ValueError(
                f"Expected 10 carriers, found {len(carriers)}. "
                "Seed master data first."
            )

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

        services = connection.execute(
            """
            SELECT service_level_id
            FROM service_levels
            WHERE service_level_id IN (
                'SVC-000001', 'SVC-000002', 'SVC-000003'
            )
            ORDER BY service_level_id
            """
        ).fetchall()

        if len(services) != 3:
            raise ValueError("Expected three configured service levels.")

        existing_routes = connection.execute(
            """
            SELECT carrier_id, service_level_id, service_zone
            FROM carrier_service_zones
            """
        ).fetchall()

        existing_route_set = set(existing_routes)

        row = connection.execute(
            """
            SELECT MAX(
                CAST(SUBSTR(carrier_service_zone_id, 5) AS INTEGER)
            )
            FROM carrier_service_zones
            WHERE carrier_service_zone_id LIKE 'CSZ-%'
            """
        ).fetchone()

        sequence = (row[0] or 0) + 1
        route_records = []

        for carrier_index, (carrier_id,) in enumerate(carriers):
            for zone_index, zone in enumerate(ZONES):
                if (carrier_index + zone_index) % 4 == 0:
                    service_id = "SVC-000002"
                elif (carrier_index + zone_index) % 2 == 0:
                    service_id = "SVC-000001"
                else:
                    service_id = "SVC-000003"

                route_key = (carrier_id, service_id, zone)

                if route_key in existing_route_set:
                    continue

                route_records.append(
                    (
                        f"CSZ-{sequence:06d}",
                        carrier_id,
                        service_id,
                        zone,
                        1,
                    )
                )

                existing_route_set.add(route_key)
                sequence += 1

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
            ORDER BY c.carrier_name, s.service_name, z.service_zone
            """
        ).fetchall()

    print(f"Database: {target_database}")
    print(f"Delivery services found: {len(services)}")
    print(f"Carrier-zone service routes found: {len(routes)}")


if __name__ == "__main__":
    seed_carrier_services()

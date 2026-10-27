
import sqlite3
from pathlib import Path

from src import init_db
from src.persist_allocations import persist_order_allocation


def create_test_database(database_file, monkeypatch):
    """Create an isolated database using the project's real schema."""
    monkeypatch.setattr(init_db, "DATABASE_FILE", database_file)

    schema_file = Path(init_db.SCHEMA_FILE)
    schema = schema_file.read_text(encoding="utf-8")

    with sqlite3.connect(database_file) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(schema)

    return database_file


def test_already_allocated_order_is_not_persisted_twice(
    tmp_path, monkeypatch
):
    database_file = tmp_path / "test_fulfillment.db"

    with sqlite3.connect(database_file) as connection:
        connection.execute("""
            CREATE TABLE orders (
                order_id TEXT PRIMARY KEY,
                order_status TEXT NOT NULL
            )
        """)
        connection.execute(
            "INSERT INTO orders (order_id, order_status) VALUES (?, ?)",
            ("ORD-2026-000001", "ALLOCATED"),
        )

    monkeypatch.setattr(init_db, "DATABASE_FILE", database_file)

    order = {
        "order_id": "ORD-2026-000001",
        "order_timestamp": "2026-10-26T12:00:00",
        "destination_zone": "SOUTH",
        "order_lines": [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
                "quantity": 1,
            }
        ],
    }

    allocations = [
        {
            "order_line_id": "LINE-000001",
            "sku_id": "SKU-000001",
            "quantity": 1,
            "node_id": "FUL-2026-000001",
        }
    ]

    result = persist_order_allocation(order, allocations)

    assert result is False

    with sqlite3.connect(database_file) as connection:
        status = connection.execute(
            "SELECT order_status FROM orders WHERE order_id = ?",
            ("ORD-2026-000001",),
        ).fetchone()[0]

    assert status == "ALLOCATED"


def test_new_order_is_persisted_successfully(tmp_path, monkeypatch):
    database_file = tmp_path / "test_fulfillment.db"
    create_test_database(database_file, monkeypatch)

    # Insert the master data and order records needed for this test.
    with sqlite3.connect(database_file) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        connection.execute(
            """
            INSERT INTO skus (
                sku_id, sku_name, category, unit_weight_kg, is_active
            )
            VALUES ('SKU-000001', 'Laptop', 'Electronics', 1.8, 1)
            """
        )

        connection.execute(
            """
            INSERT INTO fulfillment_nodes (
                node_id, node_name, city, service_zone, is_active
            )
            VALUES (
                'FUL-2026-000001', 'Hyderabad Warehouse',
                'Hyderabad', 'SOUTH', 1
            )
            """
        )

        connection.execute(
            """
            INSERT INTO inventory (
                inventory_id, node_id, sku_id,
                available_quantity, reserved_quantity, updated_at
            )
            VALUES (
                'INV-000001', 'FUL-2026-000001', 'SKU-000001',
                10, 0, '2026-10-26T12:00:00'
            )
            """
        )

        connection.execute(
            """
            INSERT INTO warehouse_capacity (
                capacity_id, node_id, capacity_date,
                max_order_lines, used_order_lines,
                max_units, used_units
            )
            VALUES (
                'CAP-000001', 'FUL-2026-000001', '2026-10-26',
                100, 0, 500, 0
            )
            """
        )

        connection.execute(
            """
            INSERT INTO carriers (carrier_id, carrier_name, is_active)
            VALUES ('CAR-000001', 'FastShip', 1)
            """
        )

        connection.execute(
            """
            INSERT INTO service_levels (
                service_level_id, service_name, transit_days,
                cutoff_time, is_active
            )
            VALUES ('SVC-000002', 'EXPRESS', 1, '14:00', 1)
            """
        )

        connection.execute(
            """
            INSERT INTO carrier_service_zones (
                carrier_service_zone_id, carrier_id, service_level_id,
                service_zone, is_active
            )
            VALUES (
                'CSZ-000001', 'CAR-000001', 'SVC-000002', 'SOUTH', 1
            )
            """
        )

        connection.execute(
            """
            INSERT INTO orders (
                order_id, order_timestamp, destination_city,
                destination_zone, order_status, created_at
            )
            VALUES (
                'ORD-2026-000001', '2026-10-26T12:00:00',
                'Hyderabad', 'SOUTH', 'CREATED', '2026-10-26T12:00:00'
            )
            """
        )

        connection.execute(
            """
            INSERT INTO order_lines (
                order_line_id, order_id, sku_id, quantity, unit_price
            )
            VALUES (
                'LINE-000001', 'ORD-2026-000001',
                'SKU-000001', 1, 55000.00
            )
            """
        )

    order = {
        "order_id": "ORD-2026-000001",
        "order_timestamp": "2026-10-26T12:00:00",
        "destination_zone": "SOUTH",
        "order_lines": [
            {
                "order_line_id": "LINE-000001",
                "sku_id": "SKU-000001",
                "quantity": 1,
            }
        ],
    }

    allocations = [
        {
            "order_line_id": "LINE-000001",
            "sku_id": "SKU-000001",
            "quantity": 1,
            "node_id": "FUL-2026-000001",
        }
    ]

    result = persist_order_allocation(order, allocations)

    assert result is True

    # Read the saved results from the database.
    with sqlite3.connect(database_file) as connection:
        status = connection.execute(
            "SELECT order_status FROM orders WHERE order_id = ?",
            ("ORD-2026-000001",),
        ).fetchone()[0]

        shipment_count = connection.execute(
            "SELECT COUNT(*) FROM shipments WHERE order_id = ?",
            ("ORD-2026-000001",),
        ).fetchone()[0]

        promise_count = connection.execute(
            "SELECT COUNT(*) FROM delivery_promises WHERE order_id = ?",
            ("ORD-2026-000001",),
        ).fetchone()[0]

        reserved_quantity = connection.execute(
            """
            SELECT reserved_quantity
            FROM inventory
            WHERE node_id = 'FUL-2026-000001'
              AND sku_id = 'SKU-000001'
            """
        ).fetchone()[0]

        capacity_usage = connection.execute(
            """
            SELECT used_order_lines, used_units
            FROM warehouse_capacity
            WHERE node_id = 'FUL-2026-000001'
              AND capacity_date = '2026-10-26'
            """
        ).fetchone()

    # Verify that all expected changes were saved.
    assert status == "ALLOCATED"
    assert shipment_count == 1
    assert promise_count == 1
    assert reserved_quantity == 1
    assert capacity_usage == (1, 1)

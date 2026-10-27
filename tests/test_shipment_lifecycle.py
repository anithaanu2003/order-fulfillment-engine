
import sqlite3

from src.shipment_lifecycle import record_tracking_event
from tests.test_persistence import create_test_database


def test_record_tracking_event_adds_next_sequence(
    tmp_path, monkeypatch
):
    database_file = tmp_path / "test_fulfillment.db"
    create_test_database(database_file, monkeypatch)

    with sqlite3.connect(database_file) as connection:
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
            INSERT INTO carriers (
                carrier_id, carrier_name, is_active
            )
            VALUES ('CAR-000001', 'FastShip', 1)
            """
        )

        connection.execute(
            """
            INSERT INTO service_levels (
                service_level_id, service_name, transit_days,
                cutoff_time, is_active
            )
            VALUES ('SVC-000001', 'STANDARD', 3, '17:00', 1)
            """
        )

        connection.execute(
            """
            INSERT INTO shipments (
                shipment_id, order_id, node_id, carrier_id,
                service_level_id, shipment_status, created_at
            )
            VALUES (
                'SHP-2026-000001', 'ORD-2026-000001',
                'FUL-2026-000001', 'CAR-000001',
                'SVC-000001', 'CREATED', '2026-10-26T12:00:00'
            )
            """
        )

    event_id = record_tracking_event(
        shipment_id="SHP-2026-000001",
        event_type="DISPATCHED",
        event_timestamp="2026-10-26T15:00:00",
        event_location="Hyderabad",
        event_notes="Shipment handed to carrier",
    )

    second_event_id = record_tracking_event(
        shipment_id="SHP-2026-000001",
        event_type="IN_TRANSIT",
        event_timestamp="2026-10-26T18:00:00",
        event_location="Vijayawada",
        event_notes="Shipment is moving to destination",
    )

    with sqlite3.connect(database_file) as connection:
        events = connection.execute(
            """
            SELECT tracking_event_id, event_sequence, event_type
            FROM tracking_events
            WHERE shipment_id = ?
            ORDER BY event_sequence
            """,
            ("SHP-2026-000001",),
        ).fetchall()

    assert event_id == "TRK-SHP-2026-000001-001"
    assert second_event_id == "TRK-SHP-2026-000001-002"

    assert events == [
        ("TRK-SHP-2026-000001-001", 1, "DISPATCHED"),
        ("TRK-SHP-2026-000001-002", 2, "IN_TRANSIT"),
    ]
    with sqlite3.connect(database_file) as connection:
        shipment_status = connection.execute(
        """
        SELECT shipment_status
        FROM shipments
        WHERE shipment_id = ?
        """,
        ("SHP-2026-000001",),
    ).fetchone()[0]

    assert shipment_status == "IN_TRANSIT"

def test_cannot_deliver_shipment_before_dispatch(
    tmp_path, monkeypatch
):
    database_file = tmp_path / "test_fulfillment.db"
    create_test_database(database_file, monkeypatch)

    with sqlite3.connect(database_file) as connection:
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
            INSERT INTO carriers (
                carrier_id, carrier_name, is_active
            )
            VALUES ('CAR-000001', 'FastShip', 1)
            """
        )

        connection.execute(
            """
            INSERT INTO service_levels (
                service_level_id, service_name, transit_days,
                cutoff_time, is_active
            )
            VALUES ('SVC-000001', 'STANDARD', 3, '17:00', 1)
            """
        )

        connection.execute(
            """
            INSERT INTO shipments (
                shipment_id, order_id, node_id, carrier_id,
                service_level_id, shipment_status, created_at
            )
            VALUES (
                'SHP-2026-000001', 'ORD-2026-000001',
                'FUL-2026-000001', 'CAR-000001',
                'SVC-000001', 'CREATED', '2026-10-26T12:00:00'
            )
            """
        )

    import pytest

    with pytest.raises(
        ValueError,
        match="Invalid shipment transition",
    ):
        record_tracking_event(
            shipment_id="SHP-2026-000001",
            event_type="DELIVERED",
            event_timestamp="2026-10-26T18:00:00",
            event_location="Hyderabad",
            event_notes="Attempted delivery",
        )


def test_delivery_event_updates_shipment_status(
    tmp_path, monkeypatch
):
    database_file = tmp_path / "test_delivery.db"
    create_test_database(database_file, monkeypatch)

    with sqlite3.connect(database_file) as connection:
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
            INSERT INTO carriers (
                carrier_id, carrier_name, is_active
            )
            VALUES ('CAR-000001', 'FastShip', 1)
            """
        )

        connection.execute(
            """
            INSERT INTO service_levels (
                service_level_id, service_name, transit_days,
                cutoff_time, is_active
            )
            VALUES ('SVC-000001', 'STANDARD', 3, '17:00', 1)
            """
        )

        connection.execute(
            """
            INSERT INTO shipments (
                shipment_id, order_id, node_id, carrier_id,
                service_level_id, shipment_status, created_at
            )
            VALUES (
                'SHP-2026-000001', 'ORD-2026-000001',
                'FUL-2026-000001', 'CAR-000001',
                'SVC-000001', 'CREATED', '2026-10-26T12:00:00'
            )
            """
        )

    record_tracking_event(
        shipment_id="SHP-2026-000001",
        event_type="DISPATCHED",
        event_timestamp="2026-10-26T15:00:00",
    )

    record_tracking_event(
        shipment_id="SHP-2026-000001",
        event_type="DELIVERED",
        event_timestamp="2026-10-29T12:00:00",
    )

    with sqlite3.connect(database_file) as connection:
        status = connection.execute(
            """
            SELECT shipment_status
            FROM shipments
            WHERE shipment_id = ?
            """,
            ("SHP-2026-000001",),
        ).fetchone()[0]

    assert status == "DELIVERED"
    

def test_cannot_move_created_shipment_directly_to_in_transit(
    tmp_path, monkeypatch
):
    database_file = tmp_path / "test_invalid_transition.db"
    create_test_database(database_file, monkeypatch)

    with sqlite3.connect(database_file) as connection:
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
            INSERT INTO carriers (
                carrier_id, carrier_name, is_active
            )
            VALUES ('CAR-000001', 'FastShip', 1)
            """
        )

        connection.execute(
            """
            INSERT INTO service_levels (
                service_level_id, service_name, transit_days,
                cutoff_time, is_active
            )
            VALUES ('SVC-000001', 'STANDARD', 3, '17:00', 1)
            """
        )

        connection.execute(
            """
            INSERT INTO shipments (
                shipment_id, order_id, node_id, carrier_id,
                service_level_id, shipment_status, created_at
            )
            VALUES (
                'SHP-2026-000001', 'ORD-2026-000001',
                'FUL-2026-000001', 'CAR-000001',
                'SVC-000001', 'CREATED', '2026-10-26T12:00:00'
            )
            """
        )

    import pytest

    with pytest.raises(ValueError, match="Invalid shipment transition"):
        record_tracking_event(
            shipment_id="SHP-2026-000001",
            event_type="IN_TRANSIT",
            event_timestamp="2026-10-26T18:00:00",
        )
        

def test_dispatch_event_records_dispatch_timestamp(tmp_path, monkeypatch):
    database_file = tmp_path / "test_dispatch_timestamp.db"
    create_test_database(database_file, monkeypatch)

    with sqlite3.connect(database_file) as connection:
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
            INSERT INTO carriers (
                carrier_id, carrier_name, is_active
            )
            VALUES ('CAR-000001', 'FastShip', 1)
            """
        )

        connection.execute(
            """
            INSERT INTO service_levels (
                service_level_id, service_name, transit_days,
                cutoff_time, is_active
            )
            VALUES ('SVC-000001', 'STANDARD', 3, '17:00', 1)
            """
        )

        connection.execute(
            """
            INSERT INTO shipments (
                shipment_id, order_id, node_id, carrier_id,
                service_level_id, shipment_status, created_at
            )
            VALUES (
                'SHP-2026-000001', 'ORD-2026-000001',
                'FUL-2026-000001', 'CAR-000001',
                'SVC-000001', 'CREATED', '2026-10-26T12:00:00'
            )
            """
        )

    dispatch_time = "2026-10-26T15:00:00"

    record_tracking_event(
        shipment_id="SHP-2026-000001",
        event_type="DISPATCHED",
        event_timestamp=dispatch_time,
        event_location="Hyderabad Warehouse",
    )

    with sqlite3.connect(database_file) as connection:
        row = connection.execute(
            """
            SELECT shipment_status, dispatched_at
            FROM shipments
            WHERE shipment_id = ?
            """,
            ("SHP-2026-000001",),
        ).fetchone()

    assert row == ("DISPATCHED", dispatch_time)

def test_delivery_event_records_delivery_timestamp(tmp_path, monkeypatch):
    database_file = tmp_path / "test_delivery_timestamp.db"
    create_test_database(database_file, monkeypatch)

    with sqlite3.connect(database_file) as connection:
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
            INSERT INTO carriers (
                carrier_id, carrier_name, is_active
            )
            VALUES ('CAR-000001', 'FastShip', 1)
            """
        )

        connection.execute(
            """
            INSERT INTO service_levels (
                service_level_id, service_name, transit_days,
                cutoff_time, is_active
            )
            VALUES ('SVC-000001', 'STANDARD', 3, '17:00', 1)
            """
        )

        connection.execute(
            """
            INSERT INTO shipments (
                shipment_id, order_id, node_id, carrier_id,
                service_level_id, shipment_status, created_at
            )
            VALUES (
                'SHP-2026-000001', 'ORD-2026-000001',
                'FUL-2026-000001', 'CAR-000001',
                'SVC-000001', 'CREATED', '2026-10-26T12:00:00'
            )
            """
        )

    dispatch_time = "2026-10-26T15:00:00"
    delivery_time = "2026-10-29T11:30:00"

    record_tracking_event(
        shipment_id="SHP-2026-000001",
        event_type="DISPATCHED",
        event_timestamp=dispatch_time,
        event_location="Hyderabad Warehouse",
    )

    record_tracking_event(
        shipment_id="SHP-2026-000001",
        event_type="DELIVERED",
        event_timestamp=delivery_time,
        event_location="Customer Address",
    )

    with sqlite3.connect(database_file) as connection:
        row = connection.execute(
            """
            SELECT shipment_status, dispatched_at, delivered_at
            FROM shipments
            WHERE shipment_id = ?
            """,
            ("SHP-2026-000001",),
        ).fetchone()

    assert row == ("DELIVERED", dispatch_time, delivery_time)




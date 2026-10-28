
import pytest

from src.allocate_orders import (
    get_unreserved_quantity,
    can_fulfill_order_line,
    can_accept_order,
)


def test_get_unreserved_quantity():
    inventory = {
        "available_quantity": 10,
        "reserved_quantity": 3,
    }

    assert get_unreserved_quantity(inventory) == 7


def test_can_fulfill_order_line_when_stock_is_sufficient():
    inventory = {
        "available_quantity": 10,
        "reserved_quantity": 3,
    }

    assert can_fulfill_order_line(inventory, 7) is True


def test_can_fulfill_order_line_when_stock_is_insufficient():
    inventory = {
        "available_quantity": 10,
        "reserved_quantity": 3,
    }

    assert can_fulfill_order_line(inventory, 8) is False


def test_can_accept_order_when_capacity_is_sufficient():
    capacity = {
        "max_order_lines": 100,
        "used_order_lines": 20,
        "max_units": 500,
        "used_units": 100,
    }

    assert can_accept_order(capacity, 2, 10) is True


def test_can_accept_order_when_capacity_is_insufficient():
    capacity = {
        "max_order_lines": 100,
        "used_order_lines": 99,
        "max_units": 500,
        "used_units": 490,
    }

    assert can_accept_order(capacity, 2, 10) is False


from src.allocate_orders import find_eligible_fulfillment_node


def test_no_single_warehouse_can_fulfill_order_line():
    inventory_records = [
        {
            "node_id": "FUL-2026-000001",
            "sku_id": "SKU-000001",
            "available_quantity": 4,
            "reserved_quantity": 0,
        },
        {
            "node_id": "FUL-2026-000002",
            "sku_id": "SKU-000001",
            "available_quantity": 4,
            "reserved_quantity": 0,
        },
    ]

    capacity_records = [
        {
            "node_id": "FUL-2026-000001",
            "max_order_lines": 100,
            "used_order_lines": 0,
            "max_units": 500,
            "used_units": 0,
        },
        {
            "node_id": "FUL-2026-000002",
            "max_order_lines": 100,
            "used_order_lines": 0,
            "max_units": 500,
            "used_units": 0,
        },
    ]

    selected_node = find_eligible_fulfillment_node(
        inventory_records,
        capacity_records,
        "SKU-000001",
        6,
        1,
    )

    assert selected_node is None


def test_stock_available_but_warehouse_capacity_insufficient():
    inventory_records = [
        {
            "node_id": "FUL-2026-000001",
            "sku_id": "SKU-000001",
            "available_quantity": 20,
            "reserved_quantity": 0,
        },
    ]

    capacity_records = [
        {
            "node_id": "FUL-2026-000001",
            "max_order_lines": 10,
            "used_order_lines": 10,
            "max_units": 100,
            "used_units": 100,
        },
    ]

    selected_node = find_eligible_fulfillment_node(
        inventory_records,
        capacity_records,
        "SKU-000001",
        5,
        1,
    )

    assert selected_node is None

from src.allocate_orders import allocate_order


def test_failed_order_rolls_back_inventory_and_capacity():
    inventory_records = [
        {
            "node_id": "FUL-2026-000001",
            "sku_id": "SKU-000001",
            "available_quantity": 10,
            "reserved_quantity": 0,
        },
        {
            "node_id": "FUL-2026-000001",
            "sku_id": "SKU-000002",
            "available_quantity": 2,
            "reserved_quantity": 0,
        },
    ]

    capacity_records = [
        {
            "node_id": "FUL-2026-000001",
            "max_order_lines": 10,
            "used_order_lines": 0,
            "max_units": 100,
            "used_units": 0,
        },
    ]

    original_inventory = [record.copy() for record in inventory_records]
    original_capacity = [record.copy() for record in capacity_records]

    order_lines = [
        {
            "order_line_id": "OL-001",
            "sku_id": "SKU-000001",
            "quantity": 5,
        },
        {
            "order_line_id": "OL-002",
            "sku_id": "SKU-000002",
            "quantity": 3,
        },
    ]

    result = allocate_order(
        inventory_records,
        capacity_records,
        order_lines,
    )

    assert result is None
    assert inventory_records == original_inventory
    assert capacity_records == original_capacity


def test_failed_order_returns_specific_failure_reason():
    inventory_records = [
        {
            "node_id": "FUL-2026-000001",
            "sku_id": "SKU-000001",
            "available_quantity": 2,
            "reserved_quantity": 0,
        },
    ]

    capacity_records = [
        {
            "node_id": "FUL-2026-000001",
            "max_order_lines": 10,
            "used_order_lines": 0,
            "max_units": 100,
            "used_units": 0,
        },
    ]

    order_lines = [
        {
            "order_line_id": "OL-001",
            "sku_id": "SKU-000001",
            "quantity": 5,
        },
    ]

    result, failure_reason = allocate_order(
        inventory_records,
        capacity_records,
        order_lines,
        return_failure_reason=True,
    )

    assert result is None
    assert failure_reason == "INSUFFICIENT_TOTAL_STOCK"
    assert inventory_records[0]["reserved_quantity"] == 0
    assert capacity_records[0]["used_order_lines"] == 0
    assert capacity_records[0]["used_units"] == 0

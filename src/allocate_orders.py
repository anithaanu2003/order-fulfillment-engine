

def get_unreserved_quantity(inventory_record):
    """
    Calculate stock available for new order allocations.
    """
    available_quantity = inventory_record["available_quantity"]
    reserved_quantity = inventory_record["reserved_quantity"]

    if available_quantity < 0:
        raise ValueError("Available quantity cannot be negative.")

    if reserved_quantity < 0:
        raise ValueError("Reserved quantity cannot be negative.")

    if reserved_quantity > available_quantity:
        raise ValueError(
            "Reserved quantity cannot exceed available quantity."
        )

    return available_quantity - reserved_quantity

def can_fulfill_order_line(inventory_record, requested_quantity):
    """
    Check whether inventory can satisfy an order line.
    """
    if requested_quantity <= 0:
        raise ValueError("Requested quantity must be greater than zero.")

    unreserved_quantity = get_unreserved_quantity(inventory_record)

    return unreserved_quantity >= requested_quantity



def find_fulfillment_node(inventory_records, sku_id, requested_quantity):
    """
    Select the warehouse with the least excess unreserved stock
    that can fulfill the requested SKU and quantity.
    """
    if requested_quantity <= 0:
        raise ValueError("Requested quantity must be greater than zero.")

    best_node = None
    smallest_excess = None

    for inventory in inventory_records:
        if inventory["sku_id"] != sku_id:
            continue

        if not can_fulfill_order_line(inventory, requested_quantity):
            continue

        unreserved_quantity = get_unreserved_quantity(inventory)
        excess = unreserved_quantity - requested_quantity

        if smallest_excess is None or excess < smallest_excess:
            smallest_excess = excess
            best_node = inventory["node_id"]

    return best_node


def reserve_inventory(inventory_record, requested_quantity):
    """
    Reserve inventory for an order if sufficient stock exists.
    Updates the inventory record and returns True on success.
    """
    if requested_quantity <= 0:
        raise ValueError("Requested quantity must be greater than zero.")

    if not can_fulfill_order_line(inventory_record, requested_quantity):
        return False

    inventory_record["reserved_quantity"] += requested_quantity
    return True

def can_accept_order(
    capacity_record,
    requested_order_lines,
    requested_units,
):
    """
    Check whether a warehouse has enough valid remaining capacity.
    """
    max_lines = capacity_record["max_order_lines"]
    used_lines = capacity_record["used_order_lines"]
    max_units = capacity_record["max_units"]
    used_units = capacity_record["used_units"]

    if min(max_lines, used_lines, max_units, used_units) < 0:
        raise ValueError("Capacity values cannot be negative.")

    if used_lines > max_lines or used_units > max_units:
        raise ValueError("Used capacity cannot exceed maximum capacity.")

    if requested_order_lines <= 0:
        raise ValueError("Requested order lines must be greater than zero.")

    if requested_units <= 0:
        raise ValueError("Requested units must be greater than zero.")

    remaining_lines = max_lines - used_lines
    remaining_units = max_units - used_units

    return (
        remaining_lines >= requested_order_lines
        and remaining_units >= requested_units
    )
    
def record_capacity_usage(
    capacity_record,
    requested_order_lines,
    requested_units,
):
    """
    Record warehouse capacity usage if enough capacity remains.
    """
    if not can_accept_order(
        capacity_record,
        requested_order_lines,
        requested_units,
    ):
        return False

    capacity_record["used_order_lines"] += requested_order_lines
    capacity_record["used_units"] += requested_units

    return True


def find_eligible_fulfillment_node(
    inventory_records,
    capacity_records,
    sku_id,
    requested_quantity,
    requested_order_lines,
):
    """
    Select an eligible warehouse with the least excess stock.

    A node must have:
    1. Sufficient unreserved stock for the requested SKU.
    2. Sufficient capacity for the requested lines and units.
    """
    if requested_quantity <= 0:
        raise ValueError("Requested quantity must be greater than zero.")

    if requested_order_lines <= 0:
        raise ValueError("Requested order lines must be greater than zero.")

    # Each node should have one capacity record for the selected date.
    capacity_by_node = {
        record["node_id"]: record
        for record in capacity_records
    }

    best_node = None
    smallest_excess = None

    for inventory in inventory_records:
        if inventory["sku_id"] != sku_id:
            continue

        if not can_fulfill_order_line(
            inventory,
            requested_quantity,
        ):
            continue

        node_id = inventory["node_id"]
        capacity = capacity_by_node.get(node_id)

        # The node must have a capacity record for this date.
        if capacity is None:
            continue

        if not can_accept_order(
            capacity,
            requested_order_lines,
            requested_quantity,
        ):
            continue

        unreserved_quantity = get_unreserved_quantity(inventory)
        excess = unreserved_quantity - requested_quantity

        # Prefer the node with the least excess stock.
        if smallest_excess is None or excess < smallest_excess:
            smallest_excess = excess
            best_node = node_id

    return best_node



def allocate_order_line(
    inventory_records,
    capacity_records,
    sku_id,
    requested_quantity,
):
    """
    Allocate one order line by reserving inventory and capacity.
    """
    node_id = find_eligible_fulfillment_node(
        inventory_records,
        capacity_records,
        sku_id,
        requested_quantity,
        1,
    )

    if node_id is None:
        return None

    selected_inventory = next(
        inventory
        for inventory in inventory_records
        if inventory["node_id"] == node_id
        and inventory["sku_id"] == sku_id
    )

    selected_capacity = next(
        capacity
        for capacity in capacity_records
        if capacity["node_id"] == node_id
    )

    if not reserve_inventory(selected_inventory, requested_quantity):
        return None

    if not record_capacity_usage(
        selected_capacity,
        1,
        requested_quantity,
    ):
        selected_inventory["reserved_quantity"] -= requested_quantity
        return None

    return node_id

def allocate_order(
    inventory_records,
    capacity_records,
    order_lines,
    return_failure_reason=False,
):
    """
    Allocate every line in an order.

    If any line fails, restore all in-memory inventory and
    capacity changes made while processing this order.

    By default, preserve the existing return behavior:
        success -> allocations list
        failure -> None

    When return_failure_reason=True:
        success -> (allocations, None)
        failure -> (None, reason)
    """
    def result_with_reason(allocations, reason=None):
        if return_failure_reason:
            return allocations, reason
        return allocations

    if not validate_order_lines(order_lines):
        reason = "INVALID_ORDER_LINES"
        print(f"ALLOCATION DEBUG: {reason}")
        return result_with_reason(None, reason)

    inventory_snapshot = [
        record.copy() for record in inventory_records
    ]
    capacity_snapshot = [
        record.copy() for record in capacity_records
    ]

    allocations = []

    for line in order_lines:
        sku_id = line["sku_id"]
        quantity = line["quantity"]

        node_id = allocate_order_line(
            inventory_records,
            capacity_records,
            sku_id,
            quantity,
        )

        if node_id is None:
            # Diagnose the failed SKU using the state before
            # this order began.
            matching_inventory = [
                record
                for record in inventory_snapshot
                if record["sku_id"] == sku_id
            ]

            total_unreserved = sum(
                get_unreserved_quantity(record)
                for record in matching_inventory
            )

            stock_eligible_nodes = {
                record["node_id"]
                for record in matching_inventory
                if can_fulfill_order_line(record, quantity)
            }

            # Capacity reflects any earlier lines allocated
            # during this order.
            capacity_eligible_nodes = {
                record["node_id"]
                for record in capacity_records
                if can_accept_order(record, 1, quantity)
            }

            eligible_nodes = (
                stock_eligible_nodes & capacity_eligible_nodes
            )

            if (
                not matching_inventory
                or total_unreserved < quantity
            ):
                reason = "INSUFFICIENT_TOTAL_STOCK"
            elif not stock_eligible_nodes:
                reason = "NO_NODE_HAS_ENOUGH_SKU_STOCK"
            elif not eligible_nodes:
                reason = "NO_STOCKED_NODE_HAS_CAPACITY"
            else:
                reason = "ALLOCATION_SELECTION_FAILED"

            print(
                f"ALLOCATION DEBUG: {reason}; "
                f"sku={sku_id}; quantity={quantity}; "
                f"total_unreserved={total_unreserved}; "
                f"stock_nodes={len(stock_eligible_nodes)}; "
                f"capacity_nodes={len(capacity_eligible_nodes)}; "
                f"eligible_nodes={len(eligible_nodes)}"
            )

            # Roll back all inventory changes made for this order.
            for record, snapshot in zip(
                inventory_records,
                inventory_snapshot,
            ):
                record.clear()
                record.update(snapshot)

            # Roll back all capacity changes made for this order.
            for record, snapshot in zip(
                capacity_records,
                capacity_snapshot,
            ):
                record.clear()
                record.update(snapshot)

            return result_with_reason(None, reason)

        allocations.append({
            "order_line_id": line["order_line_id"],
            "sku_id": sku_id,
            "quantity": quantity,
            "node_id": node_id,
        })

    return result_with_reason(allocations)




    


def calculate_order_units(order_lines):
    """Return the total quantity of units across all order lines."""
    if not order_lines:
        raise ValueError("Order lines cannot be empty.")

    total_units = 0

    for line in order_lines:
        quantity = line.get("quantity")

        if (
            not isinstance(quantity, int)
            or isinstance(quantity, bool)
            or quantity <= 0
        ):
            raise ValueError("Each quantity must be a positive integer.")

        total_units += quantity

    return total_units


def calculate_order_line_count(order_lines):
    """Return the number of product lines in an order."""
    if not order_lines:
        raise ValueError("Order lines cannot be empty.")

    return len(order_lines)


def validate_order_lines(order_lines):
    """Return True when order lines contain valid, unique IDs and SKUs."""
    if not isinstance(order_lines, list) or not order_lines:
        return False

    required_fields = {"order_line_id", "sku_id", "quantity"}

    if any(
        not isinstance(line, dict)
        or not required_fields.issubset(line)
        for line in order_lines
    ):
        return False

    if any(
        not isinstance(line["order_line_id"], str)
        or not line["order_line_id"].strip()
        or not isinstance(line["sku_id"], str)
        or not line["sku_id"].strip()
        for line in order_lines
    ):
        return False

    if any(
        not isinstance(line["quantity"], int)
        or isinstance(line["quantity"], bool)
        or line["quantity"] <= 0
        for line in order_lines
    ):
        return False

    line_ids = [line["order_line_id"] for line in order_lines]
    sku_ids = [line["sku_id"] for line in order_lines]

    return (
        len(line_ids) == len(set(line_ids))
        and len(sku_ids) == len(set(sku_ids))
    )









if __name__ == "__main__":
    sample_inventory = {
        "available_quantity": 10,
        "reserved_quantity": 2,
    }

    unreserved = get_unreserved_quantity(sample_inventory)
    print(f"Unreserved stock: {unreserved}")
    print(can_fulfill_order_line(sample_inventory, 5))
    print(can_fulfill_order_line(sample_inventory, 9))
    sample_warehouses = [
        {
            "node_id": "FUL-2026-000001",
            "sku_id": "SKU-000001",
            "available_quantity": 4,
            "reserved_quantity": 2,
        },
        {
            "node_id": "FUL-2026-000002",
            "sku_id": "SKU-000001",
            "available_quantity": 10,
            "reserved_quantity": 2,
        },
    ]

    selected_node = find_fulfillment_node(
        sample_warehouses,
        "SKU-000001",
        5,
    )

    print(f"Selected warehouse: {selected_node}")
    inventory_to_reserve = {
        "available_quantity": 10,
        "reserved_quantity": 2,
    }

    success = reserve_inventory(inventory_to_reserve, 5)

    print(f"Reservation successful: {success}")
    print(f"Updated inventory: {inventory_to_reserve}")
    sample_capacity = {
        "max_order_lines": 100,
        "used_order_lines": 98,
        "max_units": 500,
        "used_units": 490,
    }

    print(
        "Can accept order:",
        can_accept_order(sample_capacity, 2, 10),
    )

    print(
        "Can accept larger order:",
        can_accept_order(sample_capacity, 3, 10),
    )
    capacity_to_update = {
        "max_order_lines": 100,
        "used_order_lines": 98,
        "max_units": 500,
        "used_units": 490,
    }

    result = record_capacity_usage(capacity_to_update, 2, 10)

    print("Capacity recorded:", result)
    print("Updated capacity:", capacity_to_update)
    sample_inventory_records = [
        {
            "node_id": "FUL-2026-000001",
            "sku_id": "SKU-000001",
            "available_quantity": 10,
            "reserved_quantity": 8,
        },
        {
            "node_id": "FUL-2026-000002",
            "sku_id": "SKU-000001",
            "available_quantity": 10,
            "reserved_quantity": 2,
        },
    ]

    sample_capacity_records = [
        {
            "node_id": "FUL-2026-000001",
            "max_order_lines": 100,
            "used_order_lines": 10,
            "max_units": 500,
            "used_units": 100,
        },
        {
            "node_id": "FUL-2026-000002",
            "max_order_lines": 100,
            "used_order_lines": 20,
            "max_units": 500,
            "used_units": 100,
        },
    ]

    eligible_node = find_eligible_fulfillment_node(
        sample_inventory_records,
        sample_capacity_records,
        "SKU-000001",
        5,
        1,
    )

    print("Eligible fulfillment warehouse:", eligible_node)

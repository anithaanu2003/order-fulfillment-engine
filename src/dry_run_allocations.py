
from copy import deepcopy

from .allocate_orders import allocate_order
from .calculate_delivery_promise import calculate_delivery_dates
from .load_allocation_data import (
    load_capacity_records,
    load_inventory_records,
    load_orders_with_lines,
)
from .select_carrier_service import select_carrier_service


def run_dry_run(sample_size=10):
    """Simulate order allocations without changing database records."""
    orders = load_orders_with_lines()[:sample_size]

    # Keep all simulated changes in memory.
    inventory_records = deepcopy(load_inventory_records())
    capacity_by_date = {}

    allocated_count = 0
    failed_count = 0
    failure_reasons = {}

    print(f"Dry run started for {len(orders)} orders.")
    print("Database persistence is disabled.\n")

    for order in orders:
        service = select_carrier_service(
            order["destination_zone"]
        )

        if service is None:
            failed_count += 1
            reason = "NO_ELIGIBLE_CARRIER_SERVICE"
            failure_reasons[reason] = (
                failure_reasons.get(reason, 0) + 1
            )

            print(
                f"{order['order_id']}: FAILED - {reason}"
            )
            continue

        delivery_dates = calculate_delivery_dates(
            order["order_timestamp"],
            service["cutoff_time"],
            service["transit_days"],
        )

        dispatch_date = delivery_dates["dispatch_date"]

        if dispatch_date not in capacity_by_date:
            capacity_by_date[dispatch_date] = (
                load_capacity_records(dispatch_date)
            )

        capacity_records = capacity_by_date[dispatch_date]

        allocations, failure_reason = allocate_order(
            inventory_records,
            capacity_records,
            order["order_lines"],
            return_failure_reason=True,
        )

        if allocations is None:
            failed_count += 1

            # Count the specific reason returned by the allocator.
            reason = failure_reason or "UNKNOWN_ALLOCATION_FAILURE"

            failure_reasons[reason] = (
                failure_reasons.get(reason, 0) + 1
            )

            print(
                f"{order['order_id']}: FAILED - {reason}; "
                f"dispatch date={dispatch_date}; "
                f"order lines={len(order['order_lines'])}"
            )
            continue

        allocated_count += 1

        print(
            f"{order['order_id']}: SIMULATED "
            f"({len(allocations)} lines, "
            f"dispatch {dispatch_date})"
        )

    print("\nDry-run summary")
    print(f"Orders checked: {len(orders)}")
    print(f"Simulated allocations: {allocated_count}")
    print(f"Failed allocations: {failed_count}")
    print(f"Failure categories: {failure_reasons}")
    print("Database records changed: 0")


if __name__ == "__main__":
    run_dry_run(sample_size=2000)

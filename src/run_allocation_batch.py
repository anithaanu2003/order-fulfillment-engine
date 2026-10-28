
from copy import deepcopy
from pathlib import Path

from .allocate_orders import allocate_order
from .calculate_delivery_promise import calculate_delivery_dates_for_carrier
from .load_allocation_data import (
    load_capacity_records,
    load_inventory_records,
    load_orders_with_lines,
)
from .persist_allocations import persist_order_allocation
from .select_carrier_service import select_carrier_service


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def resolve_database_path(database_file=None):
    """Resolve the selected database without changing the default."""
    target = (
        Path(database_file)
        if database_file is not None
        else Path("data/fulfillment.db")
    )

    if not target.is_absolute():
        target = PROJECT_ROOT / target

    if not target.exists():
        raise FileNotFoundError(f"Database does not exist: {target}")

    return target


def run_allocation_batch(max_successful_allocations=10, database_file=None):
    """Persist a limited number of allocations in the selected database."""
    if (
        not isinstance(max_successful_allocations, int)
        or isinstance(max_successful_allocations, bool)
        or max_successful_allocations < 1
    ):
        raise ValueError("The allocation limit must be a positive integer.")

    target = resolve_database_path(database_file)
    db = str(target)

    orders = load_orders_with_lines(db)
    inventory_records = deepcopy(load_inventory_records(db))
    capacity_by_date = {}

    successful = 0
    failed = 0
    failure_reasons = {}

    def record_failure(reason):
        nonlocal failed
        failed += 1
        failure_reasons[reason] = failure_reasons.get(reason, 0) + 1

    print("Controlled allocation batch started.")
    print(f"Database: {target}")
    print(f"Successful allocation limit: {max_successful_allocations}")
    print(f"Created orders available: {len(orders)}\n")

    for order in orders:
        if successful >= max_successful_allocations:
            break

        service = select_carrier_service(order["destination_zone"], db)

        if service is None:
            record_failure("NO_ELIGIBLE_CARRIER_SERVICE")
            print(f"{order['order_id']}: FAILED - NO_ELIGIBLE_CARRIER_SERVICE")
            continue

        dates = calculate_delivery_dates_for_carrier(
            order_timestamp=order["order_timestamp"],
            transit_days=service["transit_days"],
            carrier_id=service["carrier_id"],
            service_zone=order["destination_zone"],
            database_file=db,
        )
        dispatch_date = dates["dispatch_date"]

        if dispatch_date not in capacity_by_date:
            capacity_by_date[dispatch_date] = load_capacity_records(
                dispatch_date, db
            )

        capacity_records = capacity_by_date[dispatch_date]

        inventory_before = deepcopy(inventory_records)
        capacity_before = deepcopy(capacity_records)

        allocations, reason = allocate_order(
            inventory_records,
            capacity_records,
            order["order_lines"],
            return_failure_reason=True,
        )

        if allocations is None:
            inventory_records = inventory_before
            capacity_by_date[dispatch_date] = capacity_before
            reason = reason or "UNKNOWN_ALLOCATION_FAILURE"
            record_failure(reason)
            print(
                f"{order['order_id']}: FAILED - {reason}; "
                f"dispatch date={dispatch_date}"
            )
            continue

        try:
            saved = persist_order_allocation(order, allocations, db)
        except Exception as error:
            inventory_records = inventory_before
            capacity_by_date[dispatch_date] = capacity_before
            reason = f"PERSISTENCE_ERROR: {type(error).__name__}"
            record_failure(reason)
            print(f"{order['order_id']}: FAILED - {reason}: {error}")
            continue

        if not saved:
            inventory_records = inventory_before
            capacity_by_date[dispatch_date] = capacity_before
            reason = "PERSISTENCE_REJECTED"
            record_failure(reason)
            print(f"{order['order_id']}: FAILED - {reason}")
            continue

        successful += 1
        inventory_records = deepcopy(load_inventory_records(db))
        capacity_by_date[dispatch_date] = load_capacity_records(
            dispatch_date, db
        )

        print(
            f"{order['order_id']}: PERSISTED "
            f"({len(allocations)} lines; dispatch {dispatch_date})"
        )

    print("\nAllocation batch summary")
    print(f"Successfully persisted: {successful}")
    print(f"Failed or rejected: {failed}")
    print(f"Failure categories: {failure_reasons}")

    return {
        "successful": successful,
        "failed": failed,
        "failure_reasons": failure_reasons,
    }


if __name__ == "__main__":
    run_allocation_batch(max_successful_allocations=25)


def generate_order_id(sequence: int, year: int = 2026) -> str:
    """Generate an order ID."""
    if sequence < 1:
        raise ValueError("Sequence must be greater than zero.")
    if year < 2000:
        raise ValueError("Year must be 2000 or later.")
    return f"ORD-{year}-{sequence:06d}"


def generate_shipment_id(sequence: int, year: int = 2026) -> str:
    """Generate a shipment ID."""
    if sequence < 1:
        raise ValueError("Sequence must be greater than zero.")
    if year < 2000:
        raise ValueError("Year must be 2000 or later.")
    return f"SHP-{year}-{sequence:06d}"

def generate_tracking_event_id(shipment_id: str, event_sequence: int) -> str:
    """Generate a tracking event ID for a shipment."""
    if not shipment_id.startswith("SHP-"):
        raise ValueError("Invalid shipment ID.")
    if event_sequence < 1:
        raise ValueError("Event sequence must be greater than zero.")
    return f"TRK-{shipment_id}-{event_sequence:03d}"


def generate_promise_id(order_id: str, version: int = 1) -> str:
    """Generate a delivery promise ID."""
    if not order_id.startswith("ORD-"):
        raise ValueError("Invalid order ID.")
    if version < 1:
        raise ValueError("Promise version must be greater than zero.")
    return f"PROM-{order_id}-{version:02d}"


if __name__ == "__main__":
    print(generate_order_id(1))
    print(generate_shipment_id(1))
    print(generate_tracking_event_id("SHP-2026-000001", 1))
    print(generate_tracking_event_id("SHP-2026-000001", 2))
    print(generate_promise_id("ORD-2026-000001", 1))

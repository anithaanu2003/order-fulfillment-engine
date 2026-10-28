
from src.calculate_delivery_promise import calculate_delivery_dates
from src.load_calendar_data import load_calendar_data


def calculate_delivery_promise_from_db(
    order_timestamp,
    cutoff_time,
    transit_days,
    carrier_id,
    database_file=None,
    service_zone=None,
    node_id=None,
):
    """
    Calculate delivery dates using saved carrier and holiday calendars.

    Optional service_zone and node_id filters ensure that only relevant
    regional and node-specific holidays are applied.
    """
    calendar_data = load_calendar_data(
        database_file=database_file,
        carrier_id=carrier_id,
        service_zone=service_zone,
        node_id=node_id,
    )

    return calculate_delivery_dates(
        order_timestamp=order_timestamp,
        cutoff_time=cutoff_time,
        transit_days=transit_days,
        holidays=calendar_data["holidays"],
        carrier_operating_days=calendar_data["carrier_operating_days"],
    )

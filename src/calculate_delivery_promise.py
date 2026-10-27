
from datetime import datetime, timedelta


def calculate_delivery_dates(order_timestamp, cutoff_time, transit_days):
    """
    Calculate dispatch and promised delivery dates.

    If the order arrives after the carrier cutoff, dispatch moves
    to the next calendar day. Transit days are then added.
    """
    order_time = datetime.fromisoformat(order_timestamp)
    cutoff = datetime.strptime(cutoff_time, "%H:%M").time()

    dispatch_date = order_time.date()

    if order_time.time() > cutoff:
        dispatch_date += timedelta(days=1)

    delivery_date = dispatch_date + timedelta(days=transit_days)

    return {
        "dispatch_date": dispatch_date.isoformat(),
        "promised_delivery_start": delivery_date.isoformat(),
        "promised_delivery_end": delivery_date.isoformat(),
    }

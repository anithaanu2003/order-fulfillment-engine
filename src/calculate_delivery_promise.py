
from datetime import datetime, timedelta


def is_business_day(date_value, holidays=None):
    """Return True when the date is a weekday and not a holiday."""
    holidays = holidays or set()
    return date_value.weekday() < 5 and date_value.isoformat() not in holidays


def next_business_day(date_value, holidays=None):
    """Return the same date if it is a business day, otherwise the next one."""
    while not is_business_day(date_value, holidays):
        date_value += timedelta(days=1)

    return date_value


def add_business_days(start_date, business_days, holidays=None):
    """Add business days, excluding weekends and configured holidays."""
    if business_days < 0:
        raise ValueError("Transit days cannot be negative.")

    current_date = start_date
    days_added = 0

    while days_added < business_days:
        current_date += timedelta(days=1)

        if is_business_day(current_date, holidays):
            days_added += 1

    return current_date


def calculate_delivery_dates(
    order_timestamp,
    cutoff_time,
    transit_days,
    holidays=None,
):
    """
    Calculate dispatch and promised delivery dates.

    After-cutoff orders move to the next day. Dispatch is then moved
    forward to a business day, and transit excludes weekends/holidays.
    """
    if not isinstance(transit_days, int) or isinstance(transit_days, bool):
        raise ValueError("Transit days must be a non-negative integer.")

    if transit_days < 0:
        raise ValueError("Transit days cannot be negative.")

    order_time = datetime.fromisoformat(order_timestamp)
    cutoff = datetime.strptime(cutoff_time, "%H:%M").time()

    dispatch_date = order_time.date()

    if order_time.time() > cutoff:
        dispatch_date += timedelta(days=1)

    dispatch_date = next_business_day(dispatch_date, holidays)

    delivery_date = add_business_days(
        dispatch_date,
        transit_days,
        holidays,
    )

    return {
        "dispatch_date": dispatch_date.isoformat(),
        "promised_delivery_start": delivery_date.isoformat(),
        "promised_delivery_end": delivery_date.isoformat(),
    }

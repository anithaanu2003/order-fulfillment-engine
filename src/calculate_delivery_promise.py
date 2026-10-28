
from datetime import date, datetime, timedelta


def _normalize_holidays(holidays=None):
    """Normalize holiday values to ISO date strings."""
    if not holidays:
        return set()

    normalized = set()

    for holiday in holidays:
        if isinstance(holiday, datetime):
            normalized.add(holiday.date().isoformat())
        elif isinstance(holiday, date):
            normalized.add(holiday.isoformat())
        elif isinstance(holiday, str):
            normalized.add(date.fromisoformat(holiday).isoformat())
        else:
            raise ValueError(
                "Holidays must contain ISO date strings or date objects."
            )

    return normalized


def is_business_day(date_value, holidays=None):
    """Return True when a date is a weekday and not a holiday."""
    holiday_dates = _normalize_holidays(holidays)

    return (
        date_value.weekday() < 5
        and date_value.isoformat() not in holiday_dates
    )


def next_business_day(date_value, holidays=None):
    """Return the same date if valid, otherwise the next business day."""
    holiday_dates = _normalize_holidays(holidays)

    while not is_business_day(date_value, holiday_dates):
        date_value += timedelta(days=1)

    return date_value


def add_business_days(start_date, business_days, holidays=None):
    """Add business days, excluding weekends and configured holidays."""
    if (
        not isinstance(business_days, int)
        or isinstance(business_days, bool)
        or business_days < 0
    ):
        raise ValueError("Transit days must be a non-negative integer.")

    holiday_dates = _normalize_holidays(holidays)
    current_date = start_date
    days_added = 0

    while days_added < business_days:
        current_date += timedelta(days=1)

        if is_business_day(current_date, holiday_dates):
            days_added += 1

    return current_date


def calculate_delivery_dates(
    order_timestamp,
    cutoff_time,
    transit_days,
    holidays=None,
    carrier_operating_days=None,
):
    """
    Calculate dispatch and promised delivery dates.

    Parameters:
        order_timestamp: ISO-formatted order timestamp.
        cutoff_time: Carrier cutoff in HH:MM format.
        transit_days: Non-negative integer number of business days.
        holidays: Optional dates excluded from business-day calculations.
        carrier_operating_days: Optional set/list of ISO dates on which
            the carrier operates. When provided, dispatch must occur on
            one of these dates as well as a valid business day.

    The optional parameter preserves compatibility with existing calls.
    """
    if (
        not isinstance(transit_days, int)
        or isinstance(transit_days, bool)
        or transit_days < 0
    ):
        raise ValueError("Transit days must be a non-negative integer.")

    try:
        order_time = datetime.fromisoformat(order_timestamp)
        cutoff = datetime.strptime(cutoff_time, "%H:%M").time()
    except (TypeError, ValueError) as error:
        raise ValueError(
            "Provide a valid ISO timestamp and cutoff in HH:MM format."
        ) from error

    holiday_dates = _normalize_holidays(holidays)
    operating_dates = None

    if carrier_operating_days is not None:
        operating_dates = {
            value.isoformat() if isinstance(value, date)
            else date.fromisoformat(value).isoformat()
            for value in carrier_operating_days
        }

    def is_carrier_dispatch_day(candidate):
        if not is_business_day(candidate, holiday_dates):
            return False

        if operating_dates is not None:
            return candidate.isoformat() in operating_dates

        return True

    dispatch_date = order_time.date()

    if order_time.time().replace(tzinfo=None) > cutoff:
        dispatch_date += timedelta(days=1)

    while not is_carrier_dispatch_day(dispatch_date):
        dispatch_date += timedelta(days=1)

    delivery_date = add_business_days(
        dispatch_date,
        transit_days,
        holiday_dates,
    )

    return {
        "dispatch_date": dispatch_date.isoformat(),
        "promised_delivery_start": delivery_date.isoformat(),
        "promised_delivery_end": delivery_date.isoformat(),
    }


def calculate_delivery_dates_with_calendar(
    order_timestamp,
    transit_days,
    holidays,
    carrier_calendar,
):
    """
    Calculate dispatch and delivery dates using date-specific carrier cutoffs.

    carrier_calendar maps ISO dates to dictionaries containing:
    is_operating and cutoff_time.
    """
    order_time = datetime.fromisoformat(order_timestamp)

    if (
        not isinstance(transit_days, int)
        or isinstance(transit_days, bool)
        or transit_days < 0
    ):
        raise ValueError("Transit days must be a non-negative integer.")

    if not carrier_calendar:
        raise ValueError("Carrier calendar cannot be empty.")

    holiday_dates = _normalize_holidays(holidays)
    calendar_dates = sorted(
        date.fromisoformat(day) for day in carrier_calendar
    )
    last_calendar_date = calendar_dates[-1]
    candidate = order_time.date()

    while candidate <= last_calendar_date:
        candidate_key = candidate.isoformat()
        entry = carrier_calendar.get(candidate_key)

        if (
            entry is not None
            and entry["is_operating"]
            and entry["cutoff_time"] is not None
            and is_business_day(candidate, holiday_dates)
        ):
            cutoff = datetime.strptime(
                entry["cutoff_time"], "%H:%M"
            ).time()

            # The cutoff matters when dispatch is on the order date.
            if (
                candidate > order_time.date()
                or order_time.time().replace(tzinfo=None) <= cutoff
            ):
                dispatch_date = candidate
                delivery_date = add_business_days(
                    dispatch_date, transit_days, holiday_dates
                )

                return {
                    "dispatch_date": dispatch_date.isoformat(),
                    "promised_delivery_start": delivery_date.isoformat(),
                    "promised_delivery_end": delivery_date.isoformat(),
                }

        candidate += timedelta(days=1)

    raise ValueError(
        "No eligible carrier dispatch date remains in the calendar."
    )

def calculate_delivery_dates_for_carrier(
    order_timestamp,
    transit_days,
    carrier_id,
    service_zone,
    database_file,
):
    """Calculate dates using the selected database's holidays and calendar."""
    from .load_calendar_data import (
        load_calendar_data,
        load_carrier_calendar,
    )

    calendar_data = load_calendar_data(
        database_file=database_file,
        carrier_id=carrier_id,
        service_zone=service_zone,
    )
    carrier_calendar = load_carrier_calendar(
        database_file=database_file,
        carrier_id=carrier_id,
    )

    return calculate_delivery_dates_with_calendar(
        order_timestamp=order_timestamp,
        transit_days=transit_days,
        holidays=calendar_data["holidays"],
        carrier_calendar=carrier_calendar,
    )


from src.calculate_delivery_promise import calculate_delivery_dates


def test_dispatch_skips_non_operating_carrier_days():
    result = calculate_delivery_dates(
        order_timestamp="2026-10-26T10:00:00",
        cutoff_time="17:00",
        transit_days=1,
        carrier_operating_days={
            "2026-10-27",
            "2026-10-28",
            "2026-10-29",
        },
    )

    assert result["dispatch_date"] == "2026-10-27"
    assert result["promised_delivery_start"] == "2026-10-28"


def test_dispatch_skips_holiday():
    result = calculate_delivery_dates(
        order_timestamp="2026-10-19T10:00:00",
        cutoff_time="17:00",
        transit_days=1,
        holidays={"2026-10-20"},
        carrier_operating_days={
            "2026-10-20",
            "2026-10-21",
            "2026-10-22",
        },
    )

    assert result["dispatch_date"] == "2026-10-21"
    assert result["promised_delivery_start"] == "2026-10-22"

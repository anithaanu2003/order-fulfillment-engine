
from src.calculate_delivery_promise import calculate_delivery_dates


def test_delivery_promise_before_cutoff():
    result = calculate_delivery_dates(
        "2026-10-26T10:00:00",
        "17:00",
        3,
    )

    assert result["dispatch_date"] == "2026-10-26"
    assert result["promised_delivery_start"] == "2026-10-29"
    assert result["promised_delivery_end"] == "2026-10-29"


def test_delivery_promise_after_cutoff():
    result = calculate_delivery_dates(
        "2026-10-26T18:00:00",
        "17:00",
        3,
    )

    assert result["dispatch_date"] == "2026-10-27"
    assert result["promised_delivery_start"] == "2026-10-30"
    assert result["promised_delivery_end"] == "2026-10-30"
    

def test_delivery_promise_skips_weekends():
    result = calculate_delivery_dates(
        "2026-10-30T10:00:00",  # Friday
        "17:00",
        2,
    )

    assert result["dispatch_date"] == "2026-10-30"
    assert result["promised_delivery_start"] == "2026-11-03"
    assert result["promised_delivery_end"] == "2026-11-03"


def test_delivery_promise_skips_holidays():
    result = calculate_delivery_dates(
        "2026-11-02T10:00:00",  # Monday
        "17:00",
        2,
        holidays={"2026-11-03"},
    )

    assert result["dispatch_date"] == "2026-11-02"
    assert result["promised_delivery_start"] == "2026-11-05"
    assert result["promised_delivery_end"] == "2026-11-05"


def test_dispatch_date_skips_weekends():
    result = calculate_delivery_dates(
        "2026-10-31T10:00:00",  # Saturday
        "17:00",
        1,
    )

    assert result["dispatch_date"] == "2026-11-02"
    assert result["promised_delivery_start"] == "2026-11-03"
    assert result["promised_delivery_end"] == "2026-11-03"

def test_dispatch_date_skips_holidays():
    result = calculate_delivery_dates(
        "2026-11-02T10:00:00",  # Monday
        "17:00",
        1,
        holidays={"2026-11-02"},
    )

    assert result["dispatch_date"] == "2026-11-03"
    assert result["promised_delivery_start"] == "2026-11-04"
    assert result["promised_delivery_end"] == "2026-11-04"

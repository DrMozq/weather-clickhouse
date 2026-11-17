from datetime import UTC, date, datetime

import pytest

from app.errors import DataError
from app.extract.open_meteo import (
    HOURLY_VARS,
    STG_COLUMNS,
    extract_open_meteo,
    target_end_date,
    to_stg_row,
    validate_response,
    year_chunks,
)

LOADED_AT = datetime(2026, 11, 17, 5, 0, tzinfo=UTC)


def response(hours: int = 2) -> dict:
    """Build a response shaped like the Open-Meteo archive endpoint."""
    return {
        "latitude": 59.94,
        "longitude": 30.31,
        "elevation": 4.0,
        "hourly_units": {"time": "iso8601", "temperature_2m": "°C"},
        "hourly": {
            "time": [f"2026-10-01T{h:02d}:00" for h in range(hours)],
            **{v: [1.0] * hours for v in HOURLY_VARS},
        },
    }


def test_year_chunks_split_at_year_boundary() -> None:
    assert year_chunks(date(2024, 11, 1), date(2026, 2, 10)) == [
        (date(2024, 11, 1), date(2024, 12, 31)),
        (date(2025, 1, 1), date(2025, 12, 31)),
        (date(2026, 1, 1), date(2026, 2, 10)),
    ]


def test_validate_response_raises_on_length_mismatch() -> None:
    data = response(hours=3)
    data["hourly"]["temperature_2m"] = [1.0, 2.0]

    with pytest.raises(DataError):
        validate_response(data)


def test_to_stg_row_matches_staging_columns() -> None:
    row = to_stg_row(
        "Санкт-Петербург", date(2026, 10, 1), date(2026, 10, 1), response(), LOADED_AT
    )

    assert len(row) == len(STG_COLUMNS)
    assert row[STG_COLUMNS.index("hourly_time")] == [
        "2026-10-01T00:00",
        "2026-10-01T01:00",
    ]


def test_year_chunks_single_day_is_one_chunk() -> None:
    d = date(2026, 5, 1)
    assert year_chunks(d, d) == [(d, d)]


def test_year_chunks_returns_empty_when_start_after_end() -> None:
    assert year_chunks(date(2026, 11, 13), date(2026, 11, 12)) == []


def test_validate_response_accepts_valid_response() -> None:
    validate_response(response())  # no exception = passed


def test_validate_response_raises_without_hourly_block() -> None:
    data = response(hours=3)
    del data["hourly"]
    with pytest.raises(DataError):
        validate_response(data)


def test_validate_response_raises_on_missing_variable() -> None:
    data = response(hours=3)
    del data["hourly"]["snowfall"]
    with pytest.raises(DataError):
        validate_response(data)


def test_target_end_date_crosses_month_boundary() -> None:
    assert target_end_date(date(2026, 3, 2)) == date(2026, 2, 25)


class FakeClient:
    """Stand-in for ApiClient: returns a prepared response and records requests."""

    def __init__(self) -> None:
        self.calls: list[dict] = []

    def get(self, path: str, params: dict | None = None) -> dict:
        self.calls.append(params or {})
        return response()


def test_extract_open_meteo_skips_city_that_is_up_to_date() -> None:
    client = FakeClient()
    tasks = [("Казань", 55.79, 49.12, date(2026, 11, 13))]

    rows = list(
        extract_open_meteo(client, tasks, date(2026, 11, 12), LOADED_AT, pause=0)  # type: ignore[arg-type]
    )

    assert rows == []
    assert client.calls == []


def test_extract_open_meteo_yields_one_row_per_year_chunk() -> None:
    client = FakeClient()
    tasks = [("Казань", 55.79, 49.12, date(2025, 12, 30))]

    rows = list(extract_open_meteo(client, tasks, date(2026, 1, 2), LOADED_AT, pause=0))  # type: ignore[arg-type]

    assert len(rows) == 2
    assert [(c["start_date"], c["end_date"]) for c in client.calls] == [
        (date(2025, 12, 30), date(2025, 12, 31)),
        (date(2026, 1, 1), date(2026, 1, 2)),
    ]

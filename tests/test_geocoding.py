from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from app.errors import DataError
from app.extract.geocoding import STG_COLUMNS, read_cities, search_city, to_stg_rows

LOADED_AT = datetime(2026, 11, 17, 5, 0, tzinfo=UTC)


def write_csv(tmp_path: Path, text: str) -> Path:
    """Write a reference CSV into a temporary folder and return its path."""
    path = tmp_path / "cities.csv"
    path.write_text(text, encoding="utf-8")
    return path


def candidate(**overrides: Any) -> dict[str, Any]:
    """Build one geocoding candidate shaped like the Open-Meteo search response."""
    cand = {
        "id": 524305,
        "name": "Мурманск",
        "latitude": 68.97,
        "longitude": 33.09,
        "elevation": 50.0,
        "feature_code": "PPLA",
        "country_code": "RU",
        "admin1_id": 524304,
        "timezone": "Europe/Moscow",
        "population": 295374,
        "country_id": 2017370,
        "country": "Россия",
        "admin1": "Мурманская Область",
    }
    cand.update(overrides)
    return cand


class FakeClient:
    """Stand-in for ApiClient: returns a prepared response and records requests."""

    def __init__(self, response: dict[str, Any]) -> None:
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self.calls.append(params or {})
        return self.response


def test_read_cities_uses_search_name_when_given(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "city,search_name\nМурманск,Murmansk\n")
    assert read_cities(path) == [("Мурманск", "Murmansk")]


def test_to_stg_rows_fills_missing_optional_fields_with_none() -> None:
    cand = candidate()
    del cand["population"]
    del cand["admin1"]

    [row] = to_stg_rows("Мурманск", "Murmansk", [cand], LOADED_AT)

    assert len(row) == len(STG_COLUMNS)
    assert row[STG_COLUMNS.index("population")] is None
    assert row[STG_COLUMNS.index("admin1")] is None


def test_search_city_raises_when_results_is_not_a_list() -> None:
    client = FakeClient({"results": "oops"})
    with pytest.raises(DataError):
        search_city(client, "Казань")  # type: ignore[arg-type]


def test_read_cities_defaults_search_name_to_city(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "city,search_name\nКазань,\n")
    assert read_cities(path) == [("Казань", "Казань")]


def test_read_cities_works_without_search_name_column(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "city\nОмск\n")
    assert read_cities(path) == [("Омск", "Омск")]


def test_read_cities_raises_on_duplicate_city(tmp_path: Path) -> None:
    path = write_csv(tmp_path, "city,search_name\nКазань,Казань\nКазань,Казань\n")
    with pytest.raises(DataError):
        read_cities(path)


def test_search_city_returns_empty_list_without_results() -> None:
    client = FakeClient({"generationtime_ms": 0.5})
    assert search_city(client, "Казань") == []  # type: ignore[arg-type]

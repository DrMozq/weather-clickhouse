import csv
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from app.errors import DataError
from app.extract.http import ApiClient

logger = logging.getLogger(__name__)

SEARCH_PATH = "search"
CANDIDATES = 10

STG_COLUMNS = [
    "city",
    "search_name",
    "id",
    "name",
    "latitude",
    "longitude",
    "elevation",
    "feature_code",
    "country_code",
    "admin1_id",
    "timezone",
    "population",
    "country_id",
    "country",
    "admin1",
    "loaded_at",
]
OPTIONAL_FIELDS = {"elevation", "admin1_id", "population", "admin1"}


def read_cities(path: Path) -> list[tuple[str, str]]:
    """Read (city, search_name) pairs from the reference CSV; search_name defaults to city."""
    cities: list[tuple[str, str]] = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            city = row["city"].strip()
            if not city:
                continue
            search_name = (row.get("search_name") or "").strip() or city
            cities.append((city, search_name))

    names = [city for city, _ in cities]
    duplicates = sorted({n for n in names if names.count(n) > 1})
    if duplicates:
        raise DataError(f"Duplicate cities in {path.name}: {duplicates}")
    return cities


def search_city(client: ApiClient, city_name: str) -> list[dict[str, Any]]:
    """Return geocoding candidates for one city name (may be empty)."""
    data = client.get(
        SEARCH_PATH,
        {
            "name": city_name,
            "count": CANDIDATES,
            "language": "ru",
            "countryCode": "RU",
        },
    )
    candidates = data.get("results")
    if not candidates:
        return []
    if not isinstance(candidates, list):
        raise DataError(
            f"Unexpected 'results' type for {city_name!r}: {type(candidates).__name__}"
        )
    return candidates


def to_stg_rows(
    city: str, search_name: str, candidates: list[dict[str, Any]], loaded_at: datetime
) -> list[tuple]:
    """Convert API candidates into rows for weather.stg_geocoding."""
    rows = []
    for cand in candidates:
        api_fields = (
            cand.get(c) if c in OPTIONAL_FIELDS else cand[c] for c in STG_COLUMNS[2:-1]
        )
        rows.append((city, search_name, *api_fields, loaded_at))
    return rows


def extract_geocoding(
    client: ApiClient,
    cities: list[tuple[str, str]],
    loaded_at: datetime,
    pause: float = 0.2,
) -> list[tuple]:
    """Geocode all cities and return staging rows for one run."""
    rows: list[tuple] = []
    not_found: list[str] = []

    for city, search_name in cities:
        candidates = search_city(client, search_name)
        time.sleep(pause)
        if not candidates:
            logger.warning("No geocoding results for %s", city)
            not_found.append(city)
            continue
        rows += to_stg_rows(city, search_name, candidates, loaded_at)

    if not rows:
        raise DataError("Geocoding returned no candidates for any city")

    logger.info(
        "Geocoded %d/%d cities, %d candidate rows",
        len(cities) - len(not_found),
        len(cities),
        len(rows),
    )
    return rows


if __name__ == "__main__":
    from datetime import UTC

    from app.config import PROJECT_ROOT, load_settings

    logging.basicConfig(level=logging.INFO)
    settings = load_settings()
    names = read_cities(PROJECT_ROOT / "reference" / "cities_ru.csv")[:3]

    with ApiClient(settings.geocoding_url) as client:
        rows = extract_geocoding(client, names, datetime.now(UTC))

    for row in rows:
        print(row[:4], "population:", row[STG_COLUMNS.index("population")])

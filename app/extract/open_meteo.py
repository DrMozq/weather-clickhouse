import logging
import time
from collections.abc import Iterator
from datetime import date, datetime, timedelta
from typing import Any

from app.errors import DataError
from app.extract.http import ApiClient

logger = logging.getLogger(__name__)

ARCHIVE_PATH = "archive"
START_DATE = date(2016, 1, 1)
ARCHIVE_DELAY_DAYS = 5

HOURLY_VARS = [
    "temperature_2m",
    "apparent_temperature",
    "relative_humidity_2m",
    "precipitation",
    "snowfall",
    "wind_speed_10m",
    "pressure_msl",
    "weather_code",
]

STG_COLUMNS = [
    "city",
    "start_date",
    "end_date",
    "latitude",
    "longitude",
    "elevation",
    "hourly_units",
    "hourly_time",
    *(f"hourly_{v}" for v in HOURLY_VARS),
    "loaded_at",
]


def target_end_date(today: date) -> date:
    """Return the last date the archive is expected to have."""
    return today - timedelta(days=ARCHIVE_DELAY_DAYS)


def year_chunks(start: date, end: date) -> list[tuple[date, date]]:
    """Split [start, end] into chunks that do not cross a calendar year."""
    chunks: list[tuple[date, date]] = []
    while start <= end:
        chunk_end = min(date(start.year, 12, 31), end)
        chunks.append((start, chunk_end))
        start = chunk_end + timedelta(days=1)
    return chunks


def validate_response(data: dict[str, Any]) -> None:
    """Raise DataError if the hourly block is incomplete or arrays differ in length."""
    hourly = data.get("hourly")
    if not isinstance(hourly, dict):
        raise DataError("Response has no 'hourly' block")

    missing = [v for v in ["time", *HOURLY_VARS] if v not in hourly]
    if missing:
        raise DataError(f"Response is missing hourly variables: {missing}")

    n_hours = len(hourly["time"])
    mismatched = {v: len(hourly[v]) for v in HOURLY_VARS if len(hourly[v]) != n_hours}
    if mismatched:
        raise DataError(f"Array lengths differ from time ({n_hours}): {mismatched}")


def fetch_period(
    client: ApiClient,
    latitude: float,
    longitude: float,
    start: date,
    end: date,
    pause: float = 0.0,
) -> Iterator[tuple[date, date, dict[str, Any]]]:
    """Fetch [start, end] in yearly chunks; yield (chunk_start, chunk_end, data)."""
    for chunk_start, chunk_end in year_chunks(start, end):
        data = client.get(
            ARCHIVE_PATH,
            {
                "latitude": latitude,
                "longitude": longitude,
                "start_date": chunk_start,
                "end_date": chunk_end,
                "hourly": ",".join(HOURLY_VARS),
            },
        )
        validate_response(data)
        yield chunk_start, chunk_end, data
        time.sleep(pause)


def to_stg_row(
    city: str, start: date, end: date, data: dict[str, Any], loaded_at: datetime
) -> tuple:
    """Convert one API response into a row for weather.stg_open_meteo."""
    hourly = data["hourly"]
    return (
        city,
        start,
        end,
        data["latitude"],
        data["longitude"],
        data["elevation"],
        data["hourly_units"],
        hourly["time"],
        *(hourly[v] for v in HOURLY_VARS),
        loaded_at,
    )


def extract_open_meteo(
    client: ApiClient,
    tasks: list[tuple[str, float, float, date]],
    end: date,
    loaded_at: datetime,
    pause: float = 0.0,
) -> Iterator[tuple]:
    """Yield stg_open_meteo rows for each (city, latitude, longitude, start) up to end."""
    for city, latitude, longitude, start in tasks:
        if start > end:
            continue  # already up to date

        for chunk_start, chunk_end, data in fetch_period(
            client, latitude, longitude, start, end, pause
        ):
            logger.info("Fetched %s %s..%s", city, chunk_start, chunk_end)
            yield to_stg_row(city, chunk_start, chunk_end, data, loaded_at)


if __name__ == "__main__":
    from datetime import UTC

    from app.config import load_settings

    logging.basicConfig(level=logging.INFO)
    settings = load_settings()

    end = date(2026, 1, 2)
    tasks = [
        (
            "Санкт-Петербург",
            59.94,
            30.31,
            date(2025, 12, 30),
        ),  # 2 chunks across new year
        ("Казань", 55.79, 49.12, date(2026, 1, 3)),  # start > end: skipped
    ]
    with ApiClient(settings.open_meteo_archive_url) as client:
        rows = list(
            extract_open_meteo(client, tasks, end, datetime.now(UTC), pause=0.5)
        )

    for row in rows:
        print(
            row[0], row[1], row[2], "hours:", len(row[STG_COLUMNS.index("hourly_time")])
        )
    print("row values:", len(rows[0]), "columns:", len(STG_COLUMNS))
    print("target end:", target_end_date(datetime.now(UTC).date()))

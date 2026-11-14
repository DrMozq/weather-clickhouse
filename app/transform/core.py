import logging
from datetime import datetime

from clickhouse_connect.driver.client import Client

from app.config import TRANSFORM_DIR
from app.db import execute_file

logger = logging.getLogger(__name__)


def load_cities(client: Client, run_ts: datetime) -> None:
    """Rebuild weather.cities from stg_geocoding rows of one run."""
    execute_file(client, TRANSFORM_DIR / "cities.sql", {"run_ts": run_ts})


def load_weather_hourly(client: Client) -> None:
    """Unnest new stg_open_meteo chunks into weather.weather_hourly."""
    execute_file(client, TRANSFORM_DIR / "weather_hourly.sql")


def load_weather_daily(client: Client) -> None:
    """Rebuild affected days of weather.weather_daily, one query per city timezone."""
    result = client.query("SELECT DISTINCT timezone FROM weather.cities FINAL")
    timezones = [row[0] for row in result.result_rows]
    for tz in timezones:
        execute_file(client, TRANSFORM_DIR / "weather_daily.sql", {"tz": tz})
    logger.info("Rebuilt weather_daily for %d timezones", len(timezones))

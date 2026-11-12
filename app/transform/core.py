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

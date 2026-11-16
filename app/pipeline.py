import logging
from datetime import UTC, datetime
from itertools import islice

from app.checks import run_checks
from app.config import CHECKS_DIR, DDL_DIR, PROJECT_ROOT, Settings
from app.db import get_client, init_db
from app.errors import RateLimitError
from app.extract.geocoding import extract_geocoding, read_cities
from app.extract.http import ApiClient
from app.extract.open_meteo import extract_open_meteo, target_end_date
from app.load.staging import load_stg_geocoding, load_stg_open_meteo
from app.state import get_weather_tasks
from app.transform.core import load_cities, load_weather_daily, load_weather_hourly

logger = logging.getLogger(__name__)

CITIES_CSV = PROJECT_ROOT / "reference" / "cities_ru.csv"


def run_init(settings: Settings) -> None:
    """Create all tables from sql/ddl."""
    client = get_client(settings.db)
    try:
        init_db(client, DDL_DIR)
    finally:
        client.close()


def cities_load(settings: Settings) -> datetime:
    """Geocode reference cities into stg_geocoding; return the run timestamp."""
    run_ts = datetime.now(UTC).replace(microsecond=0)
    logger.info("Cities load started, run_ts=%s", run_ts)

    cities = read_cities(CITIES_CSV)
    with ApiClient(settings.geocoding_url) as api:
        rows = extract_geocoding(api, cities, run_ts)

    client = get_client(settings.db)
    try:
        load_stg_geocoding(client, rows)
    finally:
        client.close()

    return run_ts


def cities_transform(settings: Settings, run_ts: datetime) -> None:
    """Rebuild weather.cities from stg_geocoding rows of run_ts."""
    client = get_client(settings.db)
    try:
        load_cities(client, run_ts)
    finally:
        client.close()


def cities_checks(settings: Settings) -> None:
    """Run cities data quality checks."""
    client = get_client(settings.db)
    try:
        run_checks(client, CHECKS_DIR, prefix="cities_")
    finally:
        client.close()


def run_cities(settings: Settings) -> None:
    """Run the whole cities pipeline (manual / CLI run)."""
    logger.info("Cities run started")
    run_ts = cities_load(settings)
    cities_transform(settings, run_ts)
    cities_checks(settings)
    logger.info("Cities run finished, run_ts=%s", run_ts)


def weather_load(settings: Settings, max_chunks: int, pause: float) -> int:
    """Load pending weather chunks into stg_open_meteo; return number of chunks."""
    run_ts = datetime.now(UTC).replace(microsecond=0)
    end = target_end_date(run_ts.date())
    logger.info("Weather load started, run_ts=%s, end=%s", run_ts, end)

    loaded = 0
    client = get_client(settings.db)
    try:
        tasks = get_weather_tasks(client)
        try:
            with ApiClient(settings.open_meteo_archive_url, timeout=60) as api:
                chunks = extract_open_meteo(api, tasks, end, run_ts, pause)
                for chunk_row in islice(chunks, max_chunks):
                    load_stg_open_meteo(client, [chunk_row])
                    loaded += 1
        except RateLimitError as e:
            logger.warning(
                "Rate limit reached after %d chunks, stopping: %s", loaded, e
            )
    finally:
        client.close()

    logger.info("Loaded %d chunks into stg_open_meteo", loaded)
    return loaded


def weather_transform(settings: Settings) -> None:
    """Unnest new staging chunks into weather_hourly and rebuild affected days."""
    client = get_client(settings.db)
    try:
        load_weather_hourly(client)
        load_weather_daily(client)
    finally:
        client.close()


def weather_checks(settings: Settings) -> None:
    """Run weather data quality checks."""
    client = get_client(settings.db)
    try:
        run_checks(client, CHECKS_DIR, prefix="weather_")
    finally:
        client.close()


def run_weather(settings: Settings, max_chunks: int, pause: float) -> None:
    """Run the whole weather pipeline (manual / CLI run)."""
    logger.info("Weather run started")
    loaded = weather_load(settings, max_chunks, pause)
    weather_transform(settings)
    weather_checks(settings)
    logger.info("Weather run finished, %d chunks loaded", loaded)

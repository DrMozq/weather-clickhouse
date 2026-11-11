import logging
from datetime import UTC, datetime

from app.checks import run_checks
from app.config import CHECKS_DIR, DDL_DIR, PROJECT_ROOT, Settings
from app.db import get_client, init_db
from app.extract.geocoding import extract_geocoding, read_cities
from app.extract.http import ApiClient
from app.load.staging import load_stg_geocoding
from app.transform.core import load_cities

logger = logging.getLogger(__name__)

CITIES_CSV = PROJECT_ROOT / "reference" / "cities_ru.csv"


def run_init(settings: Settings) -> None:
    """Create all tables from sql/ddl."""
    client = get_client(settings.db)
    try:
        init_db(client, DDL_DIR)
    finally:
        client.close()


def run_cities(settings: Settings) -> None:
    """Geocode reference cities, load staging, rebuild weather.cities and run checks."""
    run_ts = datetime.now(UTC).replace(microsecond=0)
    logger.info("Cities run started, run_ts=%s", run_ts)

    # 1. Extract
    cities = read_cities(CITIES_CSV)
    with ApiClient(settings.geocoding_url) as api:
        rows = extract_geocoding(api, cities, run_ts)

    client = get_client(settings.db)
    try:
        # 2. Load into staging
        load_stg_geocoding(client, rows)

        # 3. Transform staging -> cities
        load_cities(client, run_ts)

        # 4. Data quality checks
        run_checks(client, CHECKS_DIR, prefix="cities_")
        logger.info("Cities run finished, run_ts=%s", run_ts)

    finally:
        client.close()

import logging

from clickhouse_connect.driver.client import Client

from app.extract.geocoding import STG_COLUMNS as GEOCODING_COLUMNS
from app.extract.open_meteo import STG_COLUMNS as OPEN_METEO_COLUMNS

logger = logging.getLogger(__name__)


def _insert_rows(
    client: Client, table: str, columns: list[str], rows: list[tuple]
) -> int:
    """Insert rows into a staging table in one batch. Return the number of rows."""
    if not rows:
        return 0

    client.insert(table, rows, column_names=columns)
    logger.info("Inserted %d rows into %s", len(rows), table)
    return len(rows)


def load_stg_geocoding(client: Client, rows: list[tuple]) -> int:
    """Append one run of geocoding candidates to weather.stg_geocoding."""
    return _insert_rows(client, "stg_geocoding", GEOCODING_COLUMNS, rows)


def load_stg_open_meteo(client: Client, rows: list[tuple]) -> int:
    """Append weather chunks to weather.stg_open_meteo."""
    return _insert_rows(client, "stg_open_meteo", OPEN_METEO_COLUMNS, rows)

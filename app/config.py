import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from app.errors import ConfigError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = PROJECT_ROOT / "sql"
DDL_DIR = SQL_DIR / "ddl"
TRANSFORM_DIR = SQL_DIR / "transform"
MART_DIR = SQL_DIR / "mart"
CHECKS_DIR = SQL_DIR / "checks"


@dataclass(frozen=True)
class DbSettings:
    host: str
    port: int
    dbname: str
    user: str
    password: str = field(repr=False)


@dataclass(frozen=True)
class Settings:
    db: DbSettings
    geocoding_url: str
    open_meteo_archive_url: str


def _required(name: str, errors: list[str]) -> str:
    value = os.getenv(name, "")
    if not value:
        errors.append(f"{name} is not set")
    return value


def load_settings() -> Settings:
    load_dotenv()
    errors: list[str] = []

    host = _required("CLICKHOUSE_HOST", errors)
    port_raw = _required("CLICKHOUSE_PORT", errors)
    dbname = _required("CLICKHOUSE_DB", errors)
    user = _required("CLICKHOUSE_USER", errors)
    password = _required("CLICKHOUSE_PASSWORD", errors)
    geocoding_url = _required("GEOCODING_URL", errors)
    open_meteo_archive_url = _required("OPEN_METEO_ARCHIVE_URL", errors)

    port = 0
    if port_raw:
        try:
            port = int(port_raw)
        except ValueError:
            errors.append(f"CLICKHOUSE_PORT must be an integer, got {port_raw!r}")

    if errors:
        raise ConfigError("Invalid settings: " + "; ".join(errors))

    return Settings(
        db=DbSettings(
            host=host, port=port, dbname=dbname, user=user, password=password
        ),
        geocoding_url=geocoding_url,
        open_meteo_archive_url=open_meteo_archive_url,
    )


if __name__ == "__main__":
    print(load_settings())

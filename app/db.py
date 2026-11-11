import logging
from pathlib import Path

import clickhouse_connect
from clickhouse_connect.driver.client import Client

from app.config import DDL_DIR, DbSettings

logger = logging.getLogger(__name__)


def get_client(settings: DbSettings) -> Client:
    """Create a ClickHouse client; the caller must close it."""
    return clickhouse_connect.get_client(
        host=settings.host,
        port=settings.port,
        username=settings.user,
        password=settings.password,
        database=settings.dbname,
    )


def split_statements(sql: str) -> list[str]:
    """Split SQL by ';' (assumes no ';' inside strings or comments)."""
    return [s.strip() for s in sql.split(";") if s.strip()]


def execute_file(client: Client, path: Path, parameters: dict | None = None) -> None:
    """Execute all statements in a SQL file (no transactions in ClickHouse)."""
    for statement in split_statements(path.read_text(encoding="utf-8")):
        client.command(statement, parameters=parameters)


def fetch_file(client: Client, path: Path, limit: int) -> list[tuple]:
    """Run a single-statement SQL file and return up to `limit` rows."""
    statements = split_statements(path.read_text(encoding="utf-8"))
    if len(statements) != 1:
        raise ValueError(
            f"{path.name}: expected exactly one statement, got {len(statements)}"
        )
    result = client.query(statements[0])
    return [tuple(row) for row in result.result_rows[:limit]]


def init_db(client: Client, ddl_dir: Path) -> None:
    """Apply all DDL files from `ddl_dir` in file name order."""
    paths = sorted(ddl_dir.glob("*.sql"))
    if not paths:
        raise FileNotFoundError(f"No SQL files found in {ddl_dir.resolve()}")

    for path in paths:
        logger.info("Applying %s", path.name)
        execute_file(client, path)


if __name__ == "__main__":
    from app.config import load_settings

    logging.basicConfig(level=logging.INFO)
    settings = load_settings()
    client = get_client(settings.db)
    try:
        print(client.query("SELECT version()").result_rows)
        init_db(client, DDL_DIR)
    finally:
        client.close()

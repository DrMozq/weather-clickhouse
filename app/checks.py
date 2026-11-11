import logging
from pathlib import Path

from clickhouse_connect.driver import Client

from app.db import fetch_file
from app.errors import DataQualityError

logger = logging.getLogger(__name__)

SAMPLE_SIZE = 5


def run_checks(client: Client, checks_dir: Path, prefix: str = "") -> None:
    """Run checks in checks_dir matching prefix; raise DataQualityError if any returns rows."""
    paths = sorted(checks_dir.glob(f"{prefix}*.sql"))
    if not paths:
        raise FileNotFoundError(f"No SQL files found in {checks_dir.resolve()}")

    failed: list[str] = []
    for path in paths:
        logger.debug("Running check %s", path.stem)
        if violations := fetch_file(client, path, SAMPLE_SIZE):
            logger.error("Check %s failed, sample rows: %s", path.stem, violations)
            failed.append(path.stem)

    if failed:
        raise DataQualityError(f"Failed checks: {', '.join(failed)}")
    logger.info("All %d checks passed", len(paths))


if __name__ == "__main__":
    from app.config import CHECKS_DIR, load_settings
    from app.db import get_client

    logging.basicConfig(level=logging.DEBUG)
    settings = load_settings()
    client = get_client(settings.db)
    try:
        run_checks(client, CHECKS_DIR)
    finally:
        client.close()

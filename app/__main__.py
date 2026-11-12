import argparse
import logging
import sys

from app.config import load_settings
from app.errors import PipelineError
from app.pipeline import run_cities, run_init, run_weather

logger = logging.getLogger("app")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="python -m app", description="weather-clickhouse pipeline"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="enable debug logging"
    )
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("init", help="create tables")
    commands.add_parser("cities", help="load cities data")

    weather = commands.add_parser("weather", help="load weather data")
    weather.add_argument(
        "--max-chunks", type=int, default=350, help="max yearly chunks per run"
    )
    weather.add_argument(
        "--pause", type=float, default=20.0, help="seconds between API requests"
    )

    args = parser.parse_args(argv)
    return args


def main(argv: list[str] | None = None) -> int:
    """Entry point: parse arguments, run the command and return an exit code."""
    args = _parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        settings = load_settings()
        if args.command == "init":
            run_init(settings)
        elif args.command == "cities":
            run_cities(settings)
        elif args.command == "weather":
            run_weather(settings, args.max_chunks, args.pause)

    except PipelineError as e:
        logger.error("Pipeline failed: %s", e, exc_info=args.verbose)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

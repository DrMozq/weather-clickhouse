from datetime import timedelta

import pendulum  # type: ignore
from airflow.sdk import dag, task  # type: ignore

MAX_CHUNKS = 350  # ~26 API calls per yearly chunk, daily limit < 10 000 calls
PAUSE = 20.0  # seconds between requests, keeps under the hourly limit


@dag(
    dag_id="weather_daily",
    schedule="0 8 * * *",
    start_date=pendulum.datetime(2026, 11, 1, tz="Europe/Moscow"),
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=10)},
    tags=["weather-clickhouse"],
)
def weather_daily():
    @task(execution_timeout=timedelta(hours=3))
    def load() -> int:
        from app.config import load_settings
        from app.pipeline import weather_load

        return weather_load(load_settings(), MAX_CHUNKS, PAUSE)

    @task
    def transform() -> None:
        from app.config import load_settings
        from app.pipeline import weather_transform

        weather_transform(load_settings())

    @task
    def checks() -> None:
        from app.config import load_settings
        from app.pipeline import weather_checks

        weather_checks(load_settings())

    load() >> transform() >> checks()  # type: ignore


weather_daily()

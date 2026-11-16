from datetime import datetime

import pendulum  # type: ignore
from airflow.sdk import dag, task  # type: ignore


@dag(
    dag_id="cities",
    schedule=None,  # manual runs only
    start_date=pendulum.datetime(2026, 11, 1, tz="Europe/Moscow"),
    catchup=False,
    max_active_runs=1,
    tags=["weather-clickhouse"],
)
def cities():
    @task
    def load() -> datetime:
        from app.config import load_settings
        from app.pipeline import cities_load

        return cities_load(load_settings())

    @task
    def transform(run_ts: datetime) -> None:
        from app.config import load_settings
        from app.pipeline import cities_transform

        cities_transform(load_settings(), run_ts)

    @task
    def checks() -> None:
        from app.config import load_settings
        from app.pipeline import cities_checks

        cities_checks(load_settings())

    transform(load()) >> checks()  # type: ignore


cities()

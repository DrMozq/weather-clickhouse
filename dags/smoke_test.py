import pendulum  # type: ignore
from airflow.sdk import dag, task  # type: ignore


@dag(
    dag_id="smoke_test",
    schedule=None,  # only manual runs
    start_date=pendulum.datetime(2026, 11, 1, tz="Europe/Moscow"),
    catchup=False,
    tags=["weather-clickhouse"],
)
def smoke_test():
    @task
    def clickhouse_version() -> str:
        """Check that project code is importable and ClickHouse is reachable."""
        from app.config import load_settings
        from app.db import get_client

        client = get_client(load_settings().db)
        try:
            version = client.query("SELECT version()").result_rows[0][0]
        finally:
            client.close()
        print(f"ClickHouse version: {version}")
        return version

    clickhouse_version()


smoke_test()

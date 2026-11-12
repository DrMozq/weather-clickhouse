from datetime import date, timedelta

from clickhouse_connect.driver.client import Client

from app.extract.open_meteo import START_DATE

TASKS_QUERY = """
    SELECT c.city, c.latitude, c.longitude, w.last_date
    FROM weather.cities AS c FINAL
    LEFT JOIN (
        SELECT city, max(end_date) AS last_date
        FROM weather.stg_open_meteo
        GROUP BY city
    ) AS w ON w.city = c.city
    ORDER BY c.city
    SETTINGS join_use_nulls = 1
"""


def get_weather_tasks(client: Client) -> list[tuple[str, float, float, date]]:
    """Return (city, latitude, longitude, start_date) to fetch for every city in weather.cities."""
    result = client.query(TASKS_QUERY)
    tasks = []
    for city, latitude, longitude, last_date in result.result_rows:
        start_date = START_DATE if last_date is None else last_date + timedelta(days=1)
        tasks.append((city, latitude, longitude, start_date))
    return tasks


if __name__ == "__main__":
    from app.config import load_settings
    from app.db import get_client

    client = get_client(load_settings().db)
    try:
        tasks = get_weather_tasks(client)
        print(len(tasks), tasks[:3])
    finally:
        client.close()

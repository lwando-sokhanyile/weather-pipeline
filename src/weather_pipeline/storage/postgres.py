from collections.abc import Sequence

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from weather_pipeline.config import (
    DB_HOST,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_USER,
)


class PostgresStorage:
    def __init__(self) -> None:
        connection_url = (
            f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
            f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
        )

        self.engine: Engine = create_engine(
            connection_url,
            connect_args={"connect_timeout": 10},
        )

    def check_connection(self) -> None:
        with self.engine.connect() as connection:
            connection.execute(text("SELECT 1"))

    def upsert_weather(self, df: pd.DataFrame) -> int:
        if df.empty:
            return 0

        records: Sequence[dict] = df.to_dict(orient="records")

        sql = text(
            """
            INSERT INTO weather_data (
                city,
                date,
                temp_max_c,
                temp_min_c,
                precipitation_mm,
                windspeed_kmh,
                weathercode,
                ingested_at,
                temp_range_c
            )
            VALUES (
                :city,
                :date,
                :temp_max_c,
                :temp_min_c,
                :precipitation_mm,
                :windspeed_kmh,
                :weathercode,
                :ingested_at,
                :temp_range_c
            )
            ON CONFLICT (city, date)
            DO UPDATE SET
                temp_max_c = EXCLUDED.temp_max_c,
                temp_min_c = EXCLUDED.temp_min_c,
                precipitation_mm = EXCLUDED.precipitation_mm,
                windspeed_kmh = EXCLUDED.windspeed_kmh,
                weathercode = EXCLUDED.weathercode,
                ingested_at = EXCLUDED.ingested_at,
                temp_range_c = EXCLUDED.temp_range_c
            """
        )

        with self.engine.begin() as connection:
            connection.execute(sql, records)

        return len(records)

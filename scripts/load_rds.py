import pandas as pd
import logging
import sys
import sqlalchemy
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger(__name__)

DB_HOST     = os.getenv("DB_HOST")
DB_PORT     = os.getenv("DB_PORT", "5432")
DB_NAME     = os.getenv("DB_NAME")
DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def get_engine():
    """Create SQLAlchemy connection to RDS PostgreSQL."""
    connection_string = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    engine = sqlalchemy.create_engine(connection_string, connect_args={"connect_timeout": 10})
    return engine


def create_table(engine):
    """Create weather_data table if it doesn't exist."""
    create_sql = """
        CREATE TABLE IF NOT EXISTS weather_data (
            id               SERIAL PRIMARY KEY,
            city             VARCHAR(100) NOT NULL,
            date             DATE NOT NULL,
            temp_max_c       FLOAT,
            temp_min_c       FLOAT,
            precipitation_mm FLOAT,
            windspeed_kmh    FLOAT,
            weathercode      INT,
            ingested_at      TIMESTAMPTZ,
            temp_range_c     FLOAT,
            UNIQUE (city, date)
        );
    """
    with engine.connect() as conn:
        conn.execute(sqlalchemy.text(create_sql))
        conn.commit()
    logger.info("Table weather_data ready")


def load_to_rds(df: pd.DataFrame):
    """Load cleaned DataFrame into RDS PostgreSQL."""
    logger.info("=" * 50)
    logger.info("LOAD STAGE STARTED")

    try:
        engine = get_engine()

        # Test connection
        with engine.connect() as conn:
            conn.execute(sqlalchemy.text("SELECT 1"))
        logger.info("Database connection successful")

        # Create table if needed
        create_table(engine)

        # Upsert — insert new rows, skip duplicates
        rows_loaded = 0
        rows_skipped = 0

        with engine.connect() as conn:
            for _, row in df.iterrows():
                upsert_sql = sqlalchemy.text("""
                    INSERT INTO weather_data
                        (city, date, temp_max_c, temp_min_c,
                         precipitation_mm, windspeed_kmh,
                         weathercode, ingested_at, temp_range_c)
                    VALUES
                        (:city, :date, :temp_max_c, :temp_min_c,
                         :precipitation_mm, :windspeed_kmh,
                         :weathercode, :ingested_at, :temp_range_c)
                    ON CONFLICT (city, date) DO NOTHING;
                """)
                result = conn.execute(upsert_sql, row.to_dict())
                if result.rowcount == 1:
                    rows_loaded += 1
                else:
                    rows_skipped += 1

            conn.commit()

        logger.info(f"Rows loaded: {rows_loaded} | Rows skipped (already exist): {rows_skipped}")
        logger.info("LOAD STAGE COMPLETE")

    except Exception as e:
        logger.critical(f"LOAD STAGE FAILED: {e}")
        raise


if __name__ == "__main__":
    from fetch_weather import fetch_weather, validate, clean

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    df = fetch_weather()
    df = validate(df)
    df = clean(df)
    load_to_rds(df)
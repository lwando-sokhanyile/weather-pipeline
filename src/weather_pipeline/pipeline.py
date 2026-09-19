import logging

from weather_pipeline.ingestion.ingest import ingest_weather
from weather_pipeline.storage.postgres import PostgresStorage
from weather_pipeline.transformation.transform import transform_weather_data
from weather_pipeline.validation.quality import validate_weather_data


logger = logging.getLogger(__name__)


def run_pipeline() -> int:
    logger.info("Weather pipeline started")

    weather_df, s3_key = ingest_weather()
    logger.info("Raw weather data stored in S3: %s", s3_key)

    validate_weather_data(weather_df)
    logger.info("Weather data validation passed")

    transformed_df = transform_weather_data(weather_df)
    logger.info("Weather data transformation completed")

    postgres = PostgresStorage()
    postgres.check_connection()

    rows_written = postgres.upsert_weather(transformed_df)

    logger.info(
        "Weather pipeline completed successfully: %s rows written",
        rows_written,
    )

    return rows_written


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_pipeline()
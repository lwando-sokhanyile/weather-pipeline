from datetime import datetime, timezone

from weather_pipeline.ingestion.extract import extract_weather
from weather_pipeline.storage.s3 import S3Storage


def ingest_weather() -> tuple[object, str]:
    weather_df, raw_responses = extract_weather()

    payload = {
        "ingested_at": datetime.now(timezone.utc).isoformat(),
        "records": raw_responses,
    }

    storage = S3Storage()
    s3_key = storage.write_raw(payload)

    return weather_df, s3_key

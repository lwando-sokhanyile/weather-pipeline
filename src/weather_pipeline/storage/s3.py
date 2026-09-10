import json
from datetime import datetime, timezone

import boto3

from weather_pipeline.config import AWS_REGION, S3_BUCKET


class S3Storage:
    def __init__(self) -> None:
        self.client = boto3.client(
            "s3",
            region_name=AWS_REGION,
        )

    def write_raw(
        self,
        payload: dict,
        ingestion_time: datetime | None = None,
    ) -> str:
        ingestion_time = ingestion_time or datetime.now(timezone.utc)

        date_partition = ingestion_time.strftime("%Y-%m-%d")
        timestamp = ingestion_time.strftime("%Y%m%dT%H%M%S%fZ")

        key = (
            f"weather-pipeline/raw/"
            f"ingestion_date={date_partition}/"
            f"weather_{timestamp}.json"
        )

        body = json.dumps(
            payload,
            ensure_ascii=False,
        ).encode("utf-8")

        self.client.put_object(
            Bucket=S3_BUCKET,
            Key=key,
            Body=body,
            ContentType="application/json",
        )

        return key

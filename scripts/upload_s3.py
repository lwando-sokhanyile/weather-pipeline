import boto3
import pandas as pd
import logging
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

S3_BUCKET = os.getenv("S3_BUCKET")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")


def upload_to_s3(df: pd.DataFrame):
    """Save raw DataFrame as CSV and upload to S3."""
    logger.info("=" * 50)
    logger.info("S3 UPLOAD STAGE STARTED")

    try:
        # Create S3 client
        s3_client = boto3.client("s3", region_name=AWS_REGION)

        # Generate dated filename
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        s3_key = f"weather-pipeline/raw/{today}.csv"

        # Convert DataFrame to CSV in memory
        csv_buffer = df.to_csv(index=False)

        # Upload to S3
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=csv_buffer,
            ContentType="text/csv"
        )

        logger.info(f"File uploaded to s3://{S3_BUCKET}/{s3_key}")
        logger.info(f"Rows uploaded: {len(df)}")
        logger.info("S3 UPLOAD STAGE COMPLETE")

    except Exception as e:
        logger.critical(f"S3 UPLOAD FAILED: {e}")
        raise


if __name__ == "__main__":
    import sys
    from fetch_weather import fetch_weather, validate, clean

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    df = fetch_weather()
    df = validate(df)
    df = clean(df)
    upload_to_s3(df)
import os

from dotenv import load_dotenv


load_dotenv()


def get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Required environment variable is missing: {name}")
    return value


DB_HOST = get_required_env("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = get_required_env("DB_NAME")
DB_USER = get_required_env("DB_USER")
DB_PASSWORD = get_required_env("DB_PASSWORD")

S3_BUCKET = get_required_env("S3_BUCKET")
AWS_REGION = os.getenv("AWS_REGION", "eu-west-1")

MAIL_ID = os.getenv("MAIL_ID")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

API_URL = "https://api.open-meteo.com/v1/forecast"

REQUEST_TIMEOUT_SECONDS = 10

CITIES = [
    {"name": "Durban", "lat": -29.8587, "lon": 31.0218},
    {"name": "Cape Town", "lat": -33.9249, "lon": 18.4241},
    {"name": "Johannesburg", "lat": -26.2041, "lon": 28.0473},
    {"name": "Pretoria", "lat": -25.7449, "lon": 28.1878},
]

import logging
from datetime import datetime, timezone

import pandas as pd

from weather_pipeline.clients.open_meteo import OpenMeteoClient
from weather_pipeline.config import CITIES


logger = logging.getLogger(__name__)


def extract_weather() -> tuple[pd.DataFrame, list[dict]]:
    client = OpenMeteoClient()
    records = []
    raw_responses = []
    failed_cities = []

    for city in CITIES:
        try:
            data = client.fetch_daily_weather(
                latitude=city["lat"],
                longitude=city["lon"],
            )

            raw_responses.append(
                {
                    "city": city["name"],
                    "latitude": city["lat"],
                    "longitude": city["lon"],
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                    "response": data,
                }
            )

            daily = data["daily"]

            records.append(
                {
                    "city": city["name"],
                    "date": daily["time"][0],
                    "temp_max_c": daily["temperature_2m_max"][0],
                    "temp_min_c": daily["temperature_2m_min"][0],
                    "precipitation_mm": daily["precipitation_sum"][0],
                    "windspeed_kmh": daily["windspeed_10m_max"][0],
                    "weathercode": daily["weathercode"][0],
                    "ingested_at": datetime.now(timezone.utc),
                }
            )

            logger.info("Weather extraction succeeded for %s", city["name"])

        except Exception:
            failed_cities.append(city["name"])
            logger.exception("Weather extraction failed for %s", city["name"])

    if not records:
        raise RuntimeError("Weather extraction failed for all configured cities")

    if failed_cities:
        logger.warning(
            "Weather extraction completed with failed cities: %s",
            failed_cities,
        )

    return pd.DataFrame(records), raw_responses

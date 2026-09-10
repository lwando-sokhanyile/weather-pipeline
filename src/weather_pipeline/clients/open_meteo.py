import requests

from weather_pipeline.config import API_URL, REQUEST_TIMEOUT_SECONDS


class OpenMeteoClient:
    def __init__(self) -> None:
        self.session = requests.Session()

    def fetch_daily_weather(self, latitude: float, longitude: float) -> dict:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "windspeed_10m_max",
                "weathercode",
            ],
            "timezone": "auto",
            "forecast_days": 1,
        }

        response = self.session.get(
            API_URL,
            params=params,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        return response.json()

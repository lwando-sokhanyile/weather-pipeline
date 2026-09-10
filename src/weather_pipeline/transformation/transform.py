import pandas as pd


def transform_weather_data(df: pd.DataFrame) -> pd.DataFrame:
    transformed = df.copy()

    transformed["date"] = pd.to_datetime(
        transformed["date"],
        errors="raise",
    )

    transformed["temp_max_c"] = pd.to_numeric(
        transformed["temp_max_c"],
        errors="raise",
    )

    transformed["temp_min_c"] = pd.to_numeric(
        transformed["temp_min_c"],
        errors="raise",
    )

    transformed["precipitation_mm"] = pd.to_numeric(
        transformed["precipitation_mm"],
        errors="raise",
    )

    transformed["windspeed_kmh"] = pd.to_numeric(
        transformed["windspeed_kmh"],
        errors="raise",
    )

    transformed["weathercode"] = pd.to_numeric(
        transformed["weathercode"],
        errors="raise",
    ).astype("int64")

    transformed["temp_range_c"] = (
        transformed["temp_max_c"] - transformed["temp_min_c"]
    ).round(2)

    return transformed

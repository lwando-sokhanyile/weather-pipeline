import pandas as pd


REQUIRED_COLUMNS = [
    "city",
    "date",
    "temp_max_c",
    "temp_min_c",
    "precipitation_mm",
    "windspeed_kmh",
    "weathercode",
    "ingested_at",
]


def validate_weather_data(df: pd.DataFrame) -> None:
    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Weather data is missing required columns: {missing_columns}"
        )

    if df.empty:
        raise ValueError("Weather dataset is empty")

    critical_columns = [
        "city",
        "date",
        "temp_max_c",
        "temp_min_c",
        "precipitation_mm",
        "windspeed_kmh",
        "weathercode",
    ]

    null_counts = df[critical_columns].isnull().sum()
    null_columns = null_counts[null_counts > 0]

    if not null_columns.empty:
        raise ValueError(
            f"Weather data contains null values: {null_columns.to_dict()}"
        )

    if not df["temp_max_c"].between(-60, 60).all():
        raise ValueError("temp_max_c contains values outside -60 to 60 C")

    if not df["temp_min_c"].between(-60, 60).all():
        raise ValueError("temp_min_c contains values outside -60 to 60 C")

    if (df["temp_max_c"] < df["temp_min_c"]).any():
        raise ValueError("Some rows have temp_max_c lower than temp_min_c")

    if (df["precipitation_mm"] < 0).any():
        raise ValueError("precipitation_mm contains negative values")

    if (df["windspeed_kmh"] < 0).any():
        raise ValueError("windspeed_kmh contains negative values")

    duplicate_mask = df.duplicated(subset=["city", "date"], keep=False)

    if duplicate_mask.any():
        duplicate_count = int(duplicate_mask.sum())
        raise ValueError(
            f"Weather data contains {duplicate_count} duplicate city/date rows"
        )

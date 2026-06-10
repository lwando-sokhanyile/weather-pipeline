import requests
import pandas as pd
import logging
import sys
import os
from logging.handlers import SMTPHandler
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

#=========================================================================================
#   LOGGING SETUP
#=========================================================================================
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False

file_handler = logging.FileHandler("pipiline.log")
stream_handler =logging.StreamHandler(sys.stdout)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)


#=========================================================================================
# TRIGGERING EMAIL SETUP
#=========================================================================================

MAIL_ID = os.getenv("MAIL_ID")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

if MAIL_PASSWORD and MAIL_ID:
    mail_handler = SMTPHandler(
        mailhost = ("smtp.gmail.com", 587),
        fromaddr=MAIL_ID,
        toaddrs=['sokhanyilelwando933@gmail.com'],
        subject= "Weather Pipeline Failed",
        credentials=(MAIL_ID,MAIL_PASSWORD),
        secure = ()
    )
    mail_handler.setLevel(logging.ERROR)
    logger.addHandler(mail_handler)
    logger.info("Email alert handler configured succesfully")
else:
    logger.info("Email credentials not found - alert emails disabled")

#==========================================================================================
#  CITIES
#==========================================================================================
CITIES = [
    {"name": "Durban",       "lat": -29.8587, "lon": 31.0218},
    {"name": "Cape Town",    "lat": -33.9249, "lon": 18.4241},
    {"name": "Johannesburg", "lat": -26.2041, "lon": 28.0473},
    {"name": "Pretoria",     "lat": -25.7449, "lon": 28.1878}
]

API_URL = "https://api.open-meteo.com/v1/forecast"


#==========================================================================================
#   FETCH  WEATHER
#==========================================================================================
def  fetch_weather() -> pd.DataFrame:
    """
    Fetches today's weather data for all cites
    handles errors for every city, and loggs for every error ,
    and continue running
    """
    logger.info("=" * 50)
    logger.info("FETCH STAGE STARTED")
    logger.info(f"Fetching weather for {len(CITIES)} cities")
    logger.info("=" * 50)

    records = []
    failed_cities = []

    for city in CITIES:
        try:
            logger.info(f"Fetching data for {city['name']}...")

            params = {
                "latitude":    city["lat"],
                "longitude":   city["lon"],
                "daily": [
                    "temperature_2m_max",
                    "temperature_2m_min",
                    "precipitation_sum",
                    "windspeed_10m_max",
                    "weathercode",
                ],
                "timezone":    "auto",
                "forecast_days": 1,
            }

            response = requests.get(API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            daily = data["daily"]

            records.append({
                "city":            city["name"],
                "date":            daily["time"][0],
                "temp_max_c":      daily["temperature_2m_max"][0],
                "temp_min_c":      daily["temperature_2m_min"][0],
                "precipitation_mm": daily["precipitation_sum"][0],
                "windspeed_kmh":   daily["windspeed_10m_max"][0],
                "weathercode":     daily["weathercode"][0],
                "ingested_at":     datetime.now(timezone.utc).isoformat(),
            })

            logger.info(f"{city['name']} OK — max: {daily['temperature_2m_max'][0]}°C, "
                        f"min: {daily['temperature_2m_min'][0]}°C, "
                        f"rain: {daily['precipitation_sum'][0]}mm")
            
        except requests.exceptions.Timeout:
            # If the API took too long to respond
            logger.error(f"{city['name']} FAILED — API timed out after 10 seconds")
            failed_cities.append(city["name"])

        except requests.exceptions.HTTPError as e:
            # If the API returned an error code 
            logger.error(f"{city['name']} FAILED — HTTP error: {e}")
            failed_cities.append(city["name"])

        except requests.exceptions.ConnectionError:
            # If the is no internet connection
            logger.error(f"{city['name']} FAILED — No internet connection")
            failed_cities.append(city["name"])

        except KeyError as e:
            # If the API response was missing an critical critical column
            logger.error(f"{city['name']} FAILED — Unexpected API response, missing field: {e}")
            failed_cities.append(city["name"])

        except Exception as e:
            # Catch-all for anything unexpected
            logger.error(f"{city['name']} FAILED — Unexpected error: {e}")
            failed_cities.append(city["name"])


    # Summary of fetch stage
    logger.info(f"Fetch complete — {len(records)} cities succeeded, "
                f"{len(failed_cities)} failed")
    
    if failed_cities:
        logger.warning(f"Failed cities: {failed_cities}")

    if len(records) == 0:
        logger.critical("ALL cities failed . Aborting pipeline.")
        raise RuntimeError("Fetch stage failed — no data retrieved for any city.")

    df = pd.DataFrame(records)
    logger.info("FETCH STAGE COMPLETE")
    return df 

#==========================================================================================
#   VALIDATE
#==========================================================================================
def validate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run data quality checks om fetched data dataframe.
    logs a quality  score and raises an error if critacal
    checks fail  and trigger the airflow alert  if present
    """

    logger.info("=" * 50)
    logger.info("VALIDATION STAGE STARTED")
    logger.info("=" * 50)

    errors = []
    warnings = []

    # Checks for critical and stop the pipeline
    critical_columns = ["city", "date", "temp_max_c", "temp_min_c"]
    for col in critical_columns:
        nulls =df[col].isnull().sum()
        if nulls > 0:
            errors.append(f"Column '{col}' has {nulls} null value(s)")
            logger.error(f"NULL check FAILED — '{col}' has {nulls} null(s)")
        else:
            logger.info(f"NULL check PASSED — '{col}'")

    if not df["temp_max_c"].between(-60, 60).all():
        errors.append("temp_max_c has values outside plausible range (-60 to 60°C)")
        logger.error("Range check FAILED — temp_max_c out of range")
    else:
        logger.info("Range check PASSED — temp_max_c")

    if not df["temp_min_c"].between(-60, 60).all():
        errors.append("temp_min_c has values outside plausible range (-60 to 60°C)")
        logger.error("Range check FAILED — temp_min_c out of range")
    else:
        logger.info("Range check PASSED — temp_min_c")

    if not (df["temp_max_c"] >= df["temp_min_c"]).all():
        errors.append("Some rows have temp_max_c < temp_min_c")
        logger.error("Logic check FAILED — temp_max_c < temp_min_c in some rows")
    else:
        logger.info("Logic check PASSED — temp_max >= temp_min")

    # Checks for warning and continue, does not stop the pipeline
    if (df["precipitation_mm"] < 0).any():
        warnings.append("windspeed_kmh has nulls — will be filled in clean stage")
        logger.warning("precipitation_mm has negative values")

    if df["windspeed_kmh"].isnull().any():
        warnings.append("windspeed_kmh has nulls — will be filled in clean stage")
        logger.warning("windspeed_kmh has null values")

    # Data  quality checks 
    total_cells = len(df) * len(critical_columns)
    null_cells = df[critical_columns].isnull().sum().sum()
    passed_cells = total_cells - null_cells
    quality_score = round((passed_cells / total_cells) * 100, 2)

    logger.info(f"Data quality score: {quality_score}%")
    logger.info(f"Rows: {len(df)} | Cities: {df['city'].nunique()} | "
                f"Columns: {len(df.columns)}")

    if warnings:
        for w in warnings:
            logger.warning(f"Warning: {w}")

    # If any critical errors found, stop the pipeline
    if errors:
        error_msg = "Validation failed:\n" + "\n".join(errors)
        logger.critical(error_msg)
        raise ValueError(error_msg)

    logger.info("VALIDATION STAGE COMPLETE — all critical checks passed")
    return df


#==========================================================================================
#  CLEAN
#==========================================================================================
def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleaning the data frame to prepare it load to DataFrame for loading to the the database
    apply logging
    """
    logger.info("=" * 50)
    logger.info("CLEAN STAGE STARTED")
    logger.info("=" * 50)

    original_rows = len(df)

    # Remove duplicates 
    df = df.drop_duplicates(subset=["city", "date"])
    dropped = original_rows - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} duplicate row(s)")
    else:
        logger.info("No duplicates found")

    # Fix negative precipitation
    negative_precip = (df["precipitation_mm"] < 0).sum()
    if negative_precip > 0:
        df["precipitation_mm"] = df["precipitation_mm"].clip(lower=0)
        logger.warning(f"Clipped {negative_precip} negative precipitation value(s) to 0")

     # Fill missing precipitation with 0
    df["precipitation_mm"] = df["precipitation_mm"].fillna(0)

    # Fill missing windspeed with 0
    df["windspeed_kmh"] = df["windspeed_kmh"].fillna(0)

     # Cast types explicitly
    df["date"]             = pd.to_datetime(df["date"])
    df["temp_max_c"]       = df["temp_max_c"].astype(float)
    df["temp_min_c"]       = df["temp_min_c"].astype(float)
    df["precipitation_mm"] = df["precipitation_mm"].astype(float)
    df["windspeed_kmh"]    = df["windspeed_kmh"].astype(float)
    df["weathercode"]      = df["weathercode"].astype(int)
    logger.info("Types cast successfully")

    # Computed columns
    df["temp_range_c"] = round(df["temp_max_c"] - df["temp_min_c"], 2)
    logger.info("Computed column added: temp_range_c")

    logger.info(f"CLEAN STAGE COMPLETE — {len(df)} rows ready for loading")
    logger.info(f"Columns: {list(df.columns)}")

    return df


#==========================================================================================
#  MAIN
#=========================================================================================
if __name__ == "__main__":
    try:
        logger.info("PIPELINE TEST RUN HAS STARTED")

        raw_df =  fetch_weather()
        validated_df = validate(raw_df)
        clean_df = clean(validated_df)

        # Preview in terminal 
        print("\n" + "=" * 50)
        print("FINAL DATA PREVIEW")
        print("=" * 50)
        print(clean_df.to_string())
        print(f"\nShape: {clean_df.shape}")

        logger.info("PIPELINE TEST RUN COMPLETE")

    except Exception as e:
        logger.critical(f"PIPELINE FAILED: {e}")
        sys.exit(1)
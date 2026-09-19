from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

default_args = {
"owner": "lwando",
"retries": 2,
"retry_delay": timedelta(minutes=5),
}

def run_weather_pipeline():
    from weather_pipeline.pipeline import run_pipeline

    run_pipeline()

with DAG(
dag_id="weather_pipeline",
default_args=default_args,
description="Daily weather data pipeline for four South African cities",
schedule="@daily",
start_date=datetime(2026, 9, 1),
catchup=False,
tags=["weather", "portfolio", "data-engineering"],
) as dag:


    run_weather_pipeline = PythonOperator(
        task_id="run_weather_pipeline",
        python_callable=run_weather_pipeline,
    )


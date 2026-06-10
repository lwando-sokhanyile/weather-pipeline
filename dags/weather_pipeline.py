from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator
import sys
import os

# Add scripts folder to path so we can import our scripts
sys.path.insert(0, '/opt/airflow/scripts')

from fetch_weather import fetch_weather, validate, clean
from load_rds import load_to_rds
from upload_s3 import upload_to_s3

# ============================================================
# DEFAULT ARGUMENTS
# Applied to every task in the DAG
# ============================================================
default_args = {
    'owner':            'lwando',
    'retries':          1,
    'retry_delay':      timedelta(minutes=5),
    'email_on_failure': False,  # We handle alerts manually in scripts
}

# ============================================================
# FAILURE ALERT
# Called automatically by Airflow if any task fails
# ============================================================
def alert_on_failure(context):
    import smtplib
    from email.mime.text import MIMEText
    from dotenv import load_dotenv
    load_dotenv()

    task_id   = context['task_instance'].task_id
    dag_id    = context['task_instance'].dag_id
    exec_date = context['execution_date']
    exception = context.get('exception', 'Unknown error')

    body = f"""
    Weather Pipeline Failed

    DAG:       {dag_id}
    Task:      {task_id}
    Date:      {exec_date}
    Error:     {exception}

    Login to Airflow to view logs: http://localhost:8080
    """

    try:
        msg = MIMEText(body)
        msg["Subject"] = f"Airflow Alert: {dag_id} — {task_id} FAILED"
        msg["From"]    = os.getenv("MAIL_ID")
        msg["To"]      = "sokhanyilelwando@gmail.com"

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(os.getenv("MAIL_ID"), os.getenv("MAIL_PASSWORD"))
        server.send_message(msg)
        server.quit()
        print(f"Alert email sent for failed task: {task_id}")

    except Exception as e:
        print(f"Failed to send alert email: {e}")


# ============================================================
# TASK FUNCTIONS
# Each task calls one function from our scripts
# ============================================================
def task_fetch(**context):
    df = fetch_weather()
    df = validate(df)
    df = clean(df)
    # Save to XCom so next tasks can use the data
    context['ti'].xcom_push(key='clean_df', value=df.to_json())


def task_load(**context):
    import pandas as pd
    json_data = context['ti'].xcom_pull(key='clean_df', task_ids='fetch_validate_clean')
    df = pd.read_json(json_data)
    df['date'] = pd.to_datetime(df['date']).dt.date
    load_to_rds(df)


def task_upload(**context):
    import pandas as pd
    json_data = context['ti'].xcom_pull(key='clean_df', task_ids='fetch_validate_clean')
    df = pd.read_json(json_data)
    df['date'] = pd.to_datetime(df['date']).dt.date
    upload_to_s3(df)


# ============================================================
# DAG DEFINITION
# ============================================================
with DAG(
    dag_id='weather_pipeline',
    default_args=default_args,
    description='Daily weather data pipeline for 4 African cities',
    schedule='@daily',
    start_date=datetime(2026, 5, 28),
    catchup=False,
    tags=['weather', 'portfolio', 'africa'],
    on_failure_callback=alert_on_failure,
) as dag:

    fetch_task = PythonOperator(
        task_id='fetch_validate_clean',
        python_callable=task_fetch,
    )

    load_task = PythonOperator(
        task_id='load_to_rds',
        python_callable=task_load,
    )

    upload_task = PythonOperator(
        task_id='upload_to_s3',
        python_callable=task_upload,
    )

    # Pipeline order: fetch → load → upload
    fetch_task >> load_task >> upload_task
FROM apache/airflow:3.2.1

COPY requirements.txt /requirements.txt

RUN pip install --no-cache-dir -r /requirements.txt

ENV PYTHONPATH="/opt/airflow/src"

COPY src /opt/airflow/src
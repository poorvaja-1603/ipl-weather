FROM apache/airflow:2.10.3

USER root
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Install custom providers and dbt-snowflake
RUN pip install --no-cache-dir \
    dbt-snowflake \
    apache-airflow-providers-airbyte \
    apache-airflow-providers-snowflake \
    apache-airflow-providers-http \
    requests

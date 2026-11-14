-- BigQuery Dataset-level access grants (run in BigQuery console or bq query)
-- Replace PROJECT with your GCP Project ID before executing.

GRANT `roles/bigquery.dataEditor` ON SCHEMA `PROJECT.raw` TO "serviceAccount:airbyte-sa@PROJECT.iam.gserviceaccount.com";
GRANT `roles/bigquery.dataEditor` ON SCHEMA `PROJECT.airbyte_internal` TO "serviceAccount:airbyte-sa@PROJECT.iam.gserviceaccount.com";

GRANT `roles/bigquery.dataViewer` ON SCHEMA `PROJECT.raw` TO "serviceAccount:dbt-sa@PROJECT.iam.gserviceaccount.com";
GRANT `roles/bigquery.dataEditor` ON SCHEMA `PROJECT.staging` TO "serviceAccount:dbt-sa@PROJECT.iam.gserviceaccount.com";
GRANT `roles/bigquery.dataEditor` ON SCHEMA `PROJECT.marts` TO "serviceAccount:dbt-sa@PROJECT.iam.gserviceaccount.com";

GRANT `roles/bigquery.dataViewer` ON SCHEMA `PROJECT.marts` TO "serviceAccount:bi-sa@PROJECT.iam.gserviceaccount.com";

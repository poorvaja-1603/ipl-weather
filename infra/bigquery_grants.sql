-- ==============================================================================
-- BigQuery Dataset-Level Permissions (Least Privilege)
-- ==============================================================================
-- Instructions:
-- Replace `PROJECT` below with your actual GCP_PROJECT_ID (e.g. `ipl-analytics-2026`).
-- Run this in the Google BigQuery SQL Studio console or via bq query.
-- ==============================================================================

-- 1. Airbyte Service Account: Data Editor on raw and airbyte_internal
GRANT `roles/bigquery.dataEditor` ON SCHEMA `PROJECT.raw`
TO "serviceAccount:airbyte-sa@PROJECT.iam.gserviceaccount.com";

GRANT `roles/bigquery.dataEditor` ON SCHEMA `PROJECT.airbyte_internal`
TO "serviceAccount:airbyte-sa@PROJECT.iam.gserviceaccount.com";

-- 2. dbt Service Account: Data Viewer on raw, Data Editor on staging and marts
GRANT `roles/bigquery.dataViewer` ON SCHEMA `PROJECT.raw`
TO "serviceAccount:dbt-sa@PROJECT.iam.gserviceaccount.com";

GRANT `roles/bigquery.dataEditor` ON SCHEMA `PROJECT.staging`
TO "serviceAccount:dbt-sa@PROJECT.iam.gserviceaccount.com";

GRANT `roles/bigquery.dataEditor` ON SCHEMA `PROJECT.marts`
TO "serviceAccount:dbt-sa@PROJECT.iam.gserviceaccount.com";

-- 3. BI Service Account: Read-only Data Viewer strictly on marts
GRANT `roles/bigquery.dataViewer` ON SCHEMA `PROJECT.marts`
TO "serviceAccount:streamlit-bi-sa@PROJECT.iam.gserviceaccount.com";

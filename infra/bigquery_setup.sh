#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:?set GCP_PROJECT_ID}"
LOCATION="${BQ_LOCATION:-US}"

echo "Setting gcloud project to ${PROJECT_ID}..."
gcloud config set project "$PROJECT_ID"

echo "Creating BigQuery datasets (raw, staging, marts, airbyte_internal)..."
for ds in raw staging marts airbyte_internal; do
  bq --location="$LOCATION" mk --dataset --if_exists=ignore "$PROJECT_ID:$ds" 2>/dev/null || \
  bq --location="$LOCATION" mk --dataset "$PROJECT_ID:$ds" || true
done

echo "Creating service accounts (airbyte-sa, dbt-sa, bi-sa)..."
for sa in airbyte-sa dbt-sa bi-sa; do
  gcloud iam service-accounts create "$sa" --display-name="$sa" || true
done

echo "Granting bigquery.jobUser role to service accounts..."
for sa in airbyte-sa dbt-sa bi-sa; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${sa}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser"
done

mkdir -p secrets
echo "Generating JSON keys in secrets/ directory..."
for sa in airbyte-sa dbt-sa bi-sa; do
  gcloud iam service-accounts keys create "secrets/${sa}.json" \
    --iam-account="${sa}@${PROJECT_ID}.iam.gserviceaccount.com" || true
done

echo "BigQuery setup complete."

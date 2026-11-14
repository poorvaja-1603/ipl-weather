#!/usr/bin/env bash
set -euo pipefail

# Check for GCP_PROJECT_ID
if [ -z "${GCP_PROJECT_ID:-}" ]; then
  echo "Error: GCP_PROJECT_ID is not set. Run: export GCP_PROJECT_ID=your-project-id"
  exit 1
fi

PROJECT_ID="$GCP_PROJECT_ID"
LOCATION="${BQ_LOCATION:-US}"

echo "=========================================================="
echo "Configuring BigQuery for Project: $PROJECT_ID ($LOCATION)"
echo "=========================================================="

# 1. Set current gcloud project
gcloud config set project "$PROJECT_ID"

# 2. Enable BigQuery API (safe if already enabled)
gcloud services enable bigquery.googleapis.com

# 3. Create BigQuery Datasets
echo "Creating BigQuery datasets..."
for ds in raw staging marts airbyte_internal; do
  bq --location="$LOCATION" mk --dataset --if_exists=ignore "$PROJECT_ID:$ds" 2>/dev/null || \
  bq --location="$LOCATION" mk --dataset "$PROJECT_ID:$ds" || true
done

# 4. Create Service Accounts
echo "Creating Service Accounts..."
for sa in airbyte-sa dbt-sa bi-sa; do
  gcloud iam service-accounts create "$sa" --display-name="$sa service account" || true
done

# 5. Grant Job User role at project level (required to run queries/jobs)
echo "Granting roles/bigquery.jobUser role..."
for sa in airbyte-sa dbt-sa bi-sa; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${sa}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/bigquery.jobUser" --condition=None || true
done

# 6. Generate JSON Keyfiles into secrets/ directory
echo "Generating JSON keys in secrets/ directory..."
mkdir -p secrets
for sa in airbyte-sa dbt-sa bi-sa; do
  key_file="secrets/${sa}.json"
  if [ ! -f "$key_file" ]; then
    gcloud iam service-accounts keys create "$key_file" \
      --iam-account="${sa}@${PROJECT_ID}.iam.gserviceaccount.com"
    echo "Created: $key_file"
  else
    echo "Key already exists: $key_file"
  fi
done

echo "=========================================================="
echo "BigQuery setup complete! Keyfiles saved in secrets/ folder."
echo "Now run the grants from infra/bigquery_grants.sql in BigQuery console."
echo "=========================================================="

# BigQuery Setup Script for Windows PowerShell
$ErrorActionPreference = "Stop"

if (-not $env:GCP_PROJECT_ID) {
    Write-Error "Error: GCP_PROJECT_ID environment variable is not set. Run: `$env:GCP_PROJECT_ID='your-project-id'"
    exit 1
}

$PROJECT_ID = $env:GCP_PROJECT_ID
$LOCATION = if ($env:BQ_LOCATION) { $env:BQ_LOCATION } else { "US" }

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Configuring BigQuery for Project: $PROJECT_ID ($LOCATION)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Set current gcloud project
gcloud config set project $PROJECT_ID

# 2. Enable BigQuery API
gcloud services enable bigquery.googleapis.com

# 3. Create BigQuery Datasets
$datasets = @("raw", "staging", "marts", "airbyte_internal")
foreach ($ds in $datasets) {
    Write-Host "Ensuring dataset exists: $ds..."
    bq --location=$LOCATION mk --dataset --if_exists=ignore "${PROJECT_ID}:${ds}"
}

# 4. Create Service Accounts
$serviceAccounts = @("airbyte-sa", "dbt-sa", "bi-sa")
foreach ($sa in $serviceAccounts) {
    Write-Host "Creating service account: $sa..."
    gcloud iam service-accounts create $sa --display-name="$sa service account" 2>$null
}

# 5. Grant Job User role at project level
foreach ($sa in $serviceAccounts) {
    Write-Host "Granting roles/bigquery.jobUser to $sa..."
    gcloud projects add-iam-policy-binding $PROJECT_ID `
        --member="serviceAccount:${sa}@${PROJECT_ID}.iam.gserviceaccount.com" `
        --role="roles/bigquery.jobUser" `
        --condition=None
}

# 6. Generate JSON Keyfiles into secrets/ directory
if (-not (Test-Path "secrets")) {
    New-Item -ItemType Directory -Path "secrets" | Out-Null
}

foreach ($sa in $serviceAccounts) {
    $keyFile = "secrets/${sa}.json"
    if (-not (Test-Path $keyFile)) {
        Write-Host "Creating key: $keyFile..."
        gcloud iam service-accounts keys create $keyFile `
            --iam-account="${sa}@${PROJECT_ID}.iam.gserviceaccount.com"
    } else {
        Write-Host "Key already exists: $keyFile"
    }
}

Write-Host "==========================================================" -ForegroundColor Green
Write-Host "BigQuery setup complete! Keyfiles saved in secrets/ folder." -ForegroundColor Green
Write-Host "Now run the grants from infra/bigquery_grants.sql in BigQuery console." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green

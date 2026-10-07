#!/usr/bin/env bash
# One-time bootstrap for CoverageIQ on GCP. Run once, as a project owner.
# Cloud Shell (https://shell.cloud.google.com) has gcloud ready; nothing
# needs installing. Safe to re-run: every step checks before it creates.
#
# It creates the things Terraform cannot create for itself:
#   1. the GCS bucket that holds Terraform state,
#   2. two service accounts: a planner (read-only) and a deployer,
#   3. a Workload Identity pool and provider so GitHub Actions can
#      authenticate as those accounts with short-lived OIDC tokens, and
#      no downloaded keys,
#   4. the IAM bindings tying GitHub's identity to each account.
# See docs/decisions/ADR-0003-gcp-workload-identity-federation.md.
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-coverageiq-510921}"
PROJECT_NUMBER="${PROJECT_NUMBER:-1084862612609}"
REGION="${REGION:-us-central1}"

# GitHub identities are bound by immutable numeric ids, not names (the
# lesson of FleetAlert's ADR-0004). From `gh api repos/mbgolden/CoverageIQ`.
GITHUB_REPOSITORY="mbgolden/CoverageIQ"
GITHUB_REPOSITORY_ID="1402040149"
GITHUB_OWNER_ID="11353267"
APPLY_ENVIRONMENT="gcp-apply"   # the GitHub Environment that gates terraform apply

STATE_BUCKET="${PROJECT_ID}-terraform-state"
POOL_ID="github"
PROVIDER_ID="coverageiq"
PLANNER="coverageiq-planner"
DEPLOYER="coverageiq-deployer"
PLANNER_EMAIL="${PLANNER}@${PROJECT_ID}.iam.gserviceaccount.com"
DEPLOYER_EMAIL="${DEPLOYER}@${PROJECT_ID}.iam.gserviceaccount.com"
POOL_NAME="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL_ID}"

say() { printf '\n==> %s\n' "$*"; }

say "Project ${PROJECT_ID} (${PROJECT_NUMBER}), region ${REGION}"
gcloud config set project "${PROJECT_ID}" >/dev/null

say "Enabling the APIs the bootstrap itself needs (Terraform enables the rest)"
gcloud services enable \
  iam.googleapis.com iamcredentials.googleapis.com sts.googleapis.com \
  cloudresourcemanager.googleapis.com serviceusage.googleapis.com storage.googleapis.com

say "Terraform state bucket gs://${STATE_BUCKET}"
if ! gcloud storage buckets describe "gs://${STATE_BUCKET}" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${STATE_BUCKET}" \
    --location="${REGION}" --uniform-bucket-level-access --public-access-prevention
fi
gcloud storage buckets update "gs://${STATE_BUCKET}" --versioning >/dev/null

say "Service accounts"
for sa in "${PLANNER}" "${DEPLOYER}"; do
  if ! gcloud iam service-accounts describe "${sa}@${PROJECT_ID}.iam.gserviceaccount.com" >/dev/null 2>&1; then
    gcloud iam service-accounts create "${sa}" --display-name="CoverageIQ ${sa#coverageiq-} (GitHub Actions)"
  fi
done

say "Planner: read the project, read and lock the state"
gcloud projects add-iam-policy-binding "${PROJECT_ID}" --condition=None --quiet \
  --member="serviceAccount:${PLANNER_EMAIL}" --role="roles/viewer" >/dev/null
gcloud storage buckets add-iam-policy-binding "gs://${STATE_BUCKET}" \
  --member="serviceAccount:${PLANNER_EMAIL}" --role="roles/storage.objectUser" >/dev/null

say "Deployer: manage this project's resources"
# Wide by action, narrow by resource: these roles are scoped to this one
# project, whose only job is CoverageIQ. projectIamAdmin is the broad one;
# it lets Terraform grant the Cloud Run runtime account its roles.
for role in \
  roles/run.admin roles/artifactregistry.admin roles/bigquery.admin \
  roles/aiplatform.admin roles/secretmanager.admin roles/storage.admin \
  roles/iam.serviceAccountAdmin roles/iam.serviceAccountUser \
  roles/serviceusage.serviceUsageAdmin roles/resourcemanager.projectIamAdmin \
  roles/monitoring.editor roles/logging.configWriter; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" --condition=None --quiet \
    --member="serviceAccount:${DEPLOYER_EMAIL}" --role="${role}" >/dev/null
done

say "Workload Identity pool ${POOL_ID} and provider ${PROVIDER_ID}"
if ! gcloud iam workload-identity-pools describe "${POOL_ID}" --location=global >/dev/null 2>&1; then
  gcloud iam workload-identity-pools create "${POOL_ID}" --location=global --display-name="GitHub Actions"
fi
# repo_env joins the repository id and the GitHub Environment, so one
# attribute can say "this repo, in the gcp-apply environment". Jobs with
# no environment get ":none".
MAPPING="google.subject=assertion.sub"
MAPPING+=",attribute.repository=assertion.repository"
MAPPING+=",attribute.repository_id=assertion.repository_id"
MAPPING+=",attribute.repo_env=assertion.repository_id+':'+(has(assertion.environment)?assertion.environment:'none')"
if ! gcloud iam workload-identity-pools providers describe "${PROVIDER_ID}" \
    --location=global --workload-identity-pool="${POOL_ID}" >/dev/null 2>&1; then
  gcloud iam workload-identity-pools providers create-oidc "${PROVIDER_ID}" \
    --location=global --workload-identity-pool="${POOL_ID}" \
    --display-name="GitHub: ${GITHUB_REPOSITORY}" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-mapping="${MAPPING}" \
    --attribute-condition="assertion.repository_owner_id=='${GITHUB_OWNER_ID}'"
fi

say "Bind GitHub identities to the service accounts"
# Any job in this repository may plan.
gcloud iam service-accounts add-iam-policy-binding "${PLANNER_EMAIL}" --quiet \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${POOL_NAME}/attribute.repository_id/${GITHUB_REPOSITORY_ID}" >/dev/null
# Only a job running in the gcp-apply environment may deploy.
gcloud iam service-accounts add-iam-policy-binding "${DEPLOYER_EMAIL}" --quiet \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${POOL_NAME}/attribute.repo_env/${GITHUB_REPOSITORY_ID}:${APPLY_ENVIRONMENT}" >/dev/null

cat <<DONE

Bootstrap complete. Now, in GitHub (Settings > Secrets and variables > Actions > Variables),
set these repository variables:

  GCP_PROJECT_ID    ${PROJECT_ID}
  GCP_REGION        ${REGION}
  GCP_WIF_PROVIDER  ${POOL_NAME}/providers/${PROVIDER_ID}
  GCP_PLAN_SA       ${PLANNER_EMAIL}
  GCP_APPLY_SA      ${DEPLOYER_EMAIL}

and create the Environment "${APPLY_ENVIRONMENT}" (Settings > Environments) with yourself
as a required reviewer. The CI plan job starts running once GCP_WIF_PROVIDER exists.

Still by hand, in the console: a budget on the billing account with alerts at 50%, 90%
and 100% of the monthly ceiling, and the Anthropic API key in Secret Manager once
Terraform has created the secret.
DONE

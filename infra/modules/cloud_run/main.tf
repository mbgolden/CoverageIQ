# The API on Cloud Run, scaling to zero. Terraform creates the service with
# a placeholder image and then ignores the image, so the deploy workflow
# owns which build is running and a plan never wants to roll it back.

variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "name" {
  type = string
}

variable "bigquery_dataset" {
  type = string
}

variable "anthropic_secret" {
  type = string
}

variable "documents_bucket" {
  type = string
}

variable "index_endpoint_id" {
  type = string
}

variable "vector_search_index" {
  type = string
}

resource "google_service_account" "runtime" {
  project      = var.project_id
  account_id   = var.name
  display_name = "CoverageIQ API runtime"
}

# What the API may do, and nothing more: query BigQuery, call Vertex AI,
# read one secret, read documents, write logs, traces and metrics.
resource "google_project_iam_member" "runtime" {
  for_each = toset([
    "roles/bigquery.jobUser",
    "roles/aiplatform.user",
    "roles/logging.logWriter",
    "roles/cloudtrace.agent",
    "roles/monitoring.metricWriter",
  ])

  project = var.project_id
  role    = each.value
  member  = google_service_account.runtime.member
}

resource "google_bigquery_dataset_iam_member" "runtime" {
  project    = var.project_id
  dataset_id = var.bigquery_dataset
  role       = "roles/bigquery.dataEditor"
  member     = google_service_account.runtime.member
}

resource "google_secret_manager_secret_iam_member" "runtime" {
  project   = var.project_id
  secret_id = var.anthropic_secret
  role      = "roles/secretmanager.secretAccessor"
  member    = google_service_account.runtime.member
}

resource "google_storage_bucket_iam_member" "runtime" {
  bucket = var.documents_bucket
  role   = "roles/storage.objectViewer"
  member = google_service_account.runtime.member
}

resource "google_cloud_run_v2_service" "api" {
  project  = var.project_id
  location = var.region
  name     = var.name
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.runtime.email

    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }

    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }
      env {
        name  = "GCP_REGION"
        value = var.region
      }
      env {
        name  = "BIGQUERY_DATASET"
        value = var.bigquery_dataset
      }
      env {
        name  = "DOCUMENTS_BUCKET"
        value = var.documents_bucket
      }
      env {
        name  = "VECTOR_SEARCH_INDEX"
        value = var.vector_search_index
      }
      env {
        name  = "VECTOR_SEARCH_INDEX_ENDPOINT"
        value = var.index_endpoint_id
      }
      env {
        name  = "ANTHROPIC_SECRET"
        value = var.anthropic_secret
      }
    }
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image,
      client,
      client_version,
    ]
  }

  depends_on = [
    google_project_iam_member.runtime,
    google_secret_manager_secret_iam_member.runtime,
  ]
}

# The demo is public. Abuse is bounded in the application (rate limit,
# length cap, daily cost guard), not at the door.
resource "google_cloud_run_v2_service_iam_member" "public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

output "url" {
  value = google_cloud_run_v2_service.api.uri
}

output "runtime_service_account" {
  value = google_service_account.runtime.email
}

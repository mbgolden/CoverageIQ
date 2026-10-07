# The secret exists so the runtime can reference it; its value is set by
# hand in the console. Terraform never holds the key.

variable "project_id" {
  type = string
}

variable "name" {
  type = string
}

resource "google_secret_manager_secret" "this" {
  project   = var.project_id
  secret_id = var.name

  replication {
    auto {}
  }
}

output "secret_id" {
  value = google_secret_manager_secret.this.secret_id
}

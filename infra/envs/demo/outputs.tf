output "api_url" {
  description = "Public URL of the Cloud Run service"
  value       = module.cloud_run.url
}

output "image_repository" {
  description = "Artifact Registry path the deploy workflow pushes images to"
  value       = module.artifact_registry.repository_url
}

output "bigquery_dataset" {
  value = module.bigquery.dataset_id
}

output "documents_bucket" {
  value = module.vector_search.documents_bucket
}

output "vector_search_index" {
  value = module.vector_search.index_id
}

output "vector_search_index_endpoint" {
  value = module.vector_search.index_endpoint_id
}

output "anthropic_secret" {
  description = "Secret Manager secret to set by hand; Terraform never knows the value"
  value       = module.secrets.secret_id
}

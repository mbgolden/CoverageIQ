# The demo environment: everything CoverageIQ needs on GCP, in one place.
# The Cloud Run image and the deployed Vector Search index are owned by
# workflows, not by Terraform (see the cloud_run and vector_search modules).

module "project_services" {
  source     = "../../modules/project_services"
  project_id = var.project_id
}

module "artifact_registry" {
  source     = "../../modules/artifact_registry"
  project_id = var.project_id
  region     = var.region
  name       = var.name_prefix

  depends_on = [module.project_services]
}

module "secrets" {
  source     = "../../modules/secrets"
  project_id = var.project_id
  name       = "${var.name_prefix}-anthropic-api-key"

  depends_on = [module.project_services]
}

module "bigquery" {
  source     = "../../modules/bigquery"
  project_id = var.project_id
  region     = var.region
  dataset_id = "coverageiq"

  depends_on = [module.project_services]
}

module "vector_search" {
  source     = "../../modules/vector_search"
  project_id = var.project_id
  region     = var.region
  name       = var.name_prefix
  dimensions = var.embedding_dimensions

  depends_on = [module.project_services]
}

module "cloud_run" {
  source              = "../../modules/cloud_run"
  project_id          = var.project_id
  region              = var.region
  name                = "${var.name_prefix}-api"
  bigquery_dataset    = module.bigquery.dataset_id
  anthropic_secret    = module.secrets.secret_id
  documents_bucket    = module.vector_search.documents_bucket
  index_endpoint_id   = module.vector_search.index_endpoint_id
  vector_search_index = module.vector_search.index_id

  depends_on = [module.project_services]
}

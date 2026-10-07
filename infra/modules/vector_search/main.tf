# Vertex AI Vector Search: the index and its endpoint, which cost nothing
# while no index is deployed. Deploying and undeploying is done on demand
# by the eval workflow, not here (ADR-0001): if Terraform owned the
# deployment, every plan would want to put it back.

variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "name" {
  type = string
}

variable "dimensions" {
  type = number
}

# Source PDFs and, later, batch index contents.
resource "google_storage_bucket" "documents" {
  project                     = var.project_id
  name                        = "${var.project_id}-documents"
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"

  versioning {
    enabled = true
  }
}

# Streaming updates need no initial contents, so the index can exist
# before any document is ingested. SHARD_SIZE_SMALL is what the cheapest
# serving machine (e2-standard-2) supports.
resource "google_vertex_ai_index" "chunks" {
  project             = var.project_id
  region              = var.region
  display_name        = "${var.name}-chunks"
  description         = "Chunk embeddings; dense ANN over plan documents"
  index_update_method = "STREAM_UPDATE"

  metadata {
    config {
      dimensions                  = var.dimensions
      approximate_neighbors_count = 50
      shard_size                  = "SHARD_SIZE_SMALL"
      distance_measure_type       = "DOT_PRODUCT_DISTANCE"
      feature_norm_type           = "UNIT_L2_NORM"

      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count    = 500
          leaf_nodes_to_search_percent = 10
        }
      }
    }
  }
}

resource "google_vertex_ai_index_endpoint" "chunks" {
  project                 = var.project_id
  region                  = var.region
  display_name            = "${var.name}-chunks"
  description             = "Deployed to on demand by the eval workflow"
  public_endpoint_enabled = true
}

output "documents_bucket" {
  value = google_storage_bucket.documents.name
}

output "index_id" {
  value = google_vertex_ai_index.chunks.id
}

output "index_endpoint_id" {
  value = google_vertex_ai_index_endpoint.chunks.id
}

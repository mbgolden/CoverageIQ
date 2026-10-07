# Document metadata, chunks with embeddings (BigQuery vector search serves
# the public demo, ADR-0001) and the eval history.

variable "project_id" {
  type = string
}

variable "region" {
  type = string
}

variable "dataset_id" {
  type = string
}

resource "google_bigquery_dataset" "this" {
  project     = var.project_id
  dataset_id  = var.dataset_id
  location    = var.region
  description = "CoverageIQ documents, chunks, embeddings and eval history"
}

# One row per ingested document version. is_current is what retrieval
# filters on, so a superseded version is never served (SCOPE.md, freshness).
resource "google_bigquery_table" "documents" {
  project             = var.project_id
  dataset_id          = google_bigquery_dataset.this.dataset_id
  table_id            = "documents"
  deletion_protection = false # re-derivable from the source PDFs

  schema = jsonencode([
    { name = "document_id", type = "STRING", mode = "REQUIRED" },
    { name = "plan_id", type = "STRING", mode = "REQUIRED" },
    { name = "plan_year", type = "INT64", mode = "REQUIRED" },
    { name = "doc_type", type = "STRING", mode = "REQUIRED", description = "sbc | formulary | prior_auth" },
    { name = "doc_version", type = "STRING", mode = "REQUIRED" },
    { name = "source_uri", type = "STRING", mode = "REQUIRED", description = "gs:// path of the PDF" },
    { name = "is_current", type = "BOOL", mode = "REQUIRED" },
    { name = "ingested_at", type = "TIMESTAMP", mode = "REQUIRED" },
  ])
}

# Mirrors coverageiq.retrieval.base.Chunk, plus the embedding.
resource "google_bigquery_table" "chunks" {
  project             = var.project_id
  dataset_id          = google_bigquery_dataset.this.dataset_id
  table_id            = "chunks"
  deletion_protection = false # re-derivable from the source PDFs

  clustering = ["plan_id", "plan_year"]

  schema = jsonencode([
    { name = "chunk_id", type = "STRING", mode = "REQUIRED" },
    { name = "document_id", type = "STRING", mode = "REQUIRED" },
    { name = "plan_id", type = "STRING", mode = "REQUIRED" },
    { name = "plan_year", type = "INT64", mode = "REQUIRED" },
    { name = "doc_type", type = "STRING", mode = "REQUIRED" },
    { name = "doc_version", type = "STRING", mode = "REQUIRED" },
    { name = "section", type = "STRING", mode = "REQUIRED" },
    { name = "page", type = "INT64", mode = "REQUIRED" },
    { name = "text", type = "STRING", mode = "REQUIRED" },
    { name = "token_count", type = "INT64", mode = "REQUIRED" },
    { name = "embedding", type = "FLOAT64", mode = "REPEATED" },
    { name = "embedding_model", type = "STRING", mode = "REQUIRED" },
    { name = "created_at", type = "TIMESTAMP", mode = "REQUIRED" },
  ])
}

# Eval history is the project's record; it is not re-derivable.
resource "google_bigquery_table" "eval_runs" {
  project             = var.project_id
  dataset_id          = google_bigquery_dataset.this.dataset_id
  table_id            = "eval_runs"
  deletion_protection = true

  schema = jsonencode([
    { name = "run_id", type = "STRING", mode = "REQUIRED" },
    { name = "started_at", type = "TIMESTAMP", mode = "REQUIRED" },
    { name = "git_sha", type = "STRING", mode = "REQUIRED" },
    { name = "backend", type = "STRING", mode = "REQUIRED", description = "bigquery | vector_search | vector_search_brute_force" },
    { name = "config", type = "JSON", mode = "NULLABLE" },
    { name = "summary", type = "JSON", mode = "NULLABLE", description = "coverageiq.evals.summarize output" },
  ])
}

resource "google_bigquery_table" "eval_scores" {
  project             = var.project_id
  dataset_id          = google_bigquery_dataset.this.dataset_id
  table_id            = "eval_scores"
  deletion_protection = true

  schema = jsonencode([
    { name = "run_id", type = "STRING", mode = "REQUIRED" },
    { name = "item_id", type = "STRING", mode = "REQUIRED" },
    { name = "question_type", type = "STRING", mode = "REQUIRED" },
    { name = "hit", type = "BOOL", mode = "REQUIRED" },
    { name = "recall", type = "FLOAT64", mode = "REQUIRED" },
    { name = "reciprocal_rank", type = "FLOAT64", mode = "REQUIRED" },
    { name = "forbidden_hit", type = "BOOL", mode = "REQUIRED" },
  ])
}

output "dataset_id" {
  value = google_bigquery_dataset.this.dataset_id
}

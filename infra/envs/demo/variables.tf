variable "project_id" {
  description = "GCP project id (not the number)"
  type        = string
  default     = "coverageiq-510921"
}

variable "region" {
  description = "Region for every regional resource"
  type        = string
  default     = "us-central1"
}

variable "name_prefix" {
  description = "Prefix for resource names, so everything this env owns is recognisable"
  type        = string
  default     = "coverageiq-demo"
}

variable "embedding_dimensions" {
  description = "Dimensions of the embedding model; fixed per index"
  type        = number
  default     = 768
}

# State lives in the bucket infra/bootstrap/bootstrap.sh creates. Object
# versioning on that bucket is the state history.
terraform {
  backend "gcs" {
    bucket = "coverageiq-510921-terraform-state"
    prefix = "envs/demo"
  }
}

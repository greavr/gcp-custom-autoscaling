# Cloud Function Code
## VPC Connector
resource "google_vpc_access_connector" "connector" {
  name          = var.vpc-connector-name
  region        = var.region
  ip_cidr_range = var.gcp-serverless
  network       = var.gcp-vpc
}

# Create Zip file
data "archive_file" "cd-autoscaler" {
  type        = "zip"
  output_path = "../artifacts/cloud_function.zip"
  source_dir = "../auto-scaler"
}

## CF Code Upload
resource "google_storage_bucket_object" "cf_code" {
  name   = "cloud_function.zip"
  bucket = google_storage_bucket.bucket.name
  source = "../artifacts/cloud_function.zip"
}

## CF Code
resource "google_cloudfunctions_function" "autoscaler-function" {
  description = "Custom Autoscaler"
  runtime     = "python37"
  region  = var.region
  name = var.cf-name

  available_memory_mb   = 128
  source_archive_bucket = google_storage_bucket.bucket.name
  source_archive_object = google_storage_bucket_object.cf_code.name
  trigger_http          = true
  timeout               = 60
  entry_point           = "MainThread"

  vpc_connector = google_vpc_access_connector.connector.name

   environment_variables = {
    "mig_name" = var.mig-name
    "mig_region" = var.region
    "upper_session_count" = var.max_sessions
    "lower_session_count" = var.min_sessions
    "new_session_lock_timeout" = var.timeout
  }

   depends_on = [google_vpc_access_connector.connector]

}

# Assign permissions to allow anon invocation
resource "google_cloudfunctions_function_iam_member" "invoker" {
  project        = var.gcp-project-name
  cloud_function = google_cloudfunctions_function.autoscaler-function.name
  role   = "roles/cloudfunctions.invoker"
  member = "allUsers"
}

# Cloud Scheduler
resource "google_cloud_scheduler_job" "check_sessions" {
  name             = "check_sessions"
  description      = "Check Server Sessions"
  schedule         = var.cron-schedule
  time_zone        = "America/New_York"
  attempt_deadline = "240s"

  retry_config {
    retry_count = 1
  }

  http_target {
    http_method = "POST"
    uri         = google_cloudfunctions_function.autoscaler-function.https_trigger_url
  }

   depends_on = [google_app_engine_application.app]
}

# Required App Engine :(
resource "google_app_engine_application" "app" {
  project     = var.gcp-project-name
  location_id = var.region
}

# Used to Upload the Set-Mig CF
# Create Zip file
data "archive_file" "set-mig" {
  type        = "zip"
  output_path = "../artifacts/set-mig.zip"
  source_dir = "../Mainual-Scaler-set-mig"
}

# Upload to GCS
resource "google_storage_bucket_object" "set-mig-code" {
  name   = "set-mig.zip"
  bucket = google_storage_bucket.bucket.name
  source = "../artifacts/set-mig.zip"
}

# Create CF
resource "google_cloudfunctions_function" "set-mig-function" {
  description = "Set MIG Size"
  runtime     = "python37"
  region  = var.region
  name = "set-mig"

  available_memory_mb   = 128
  source_archive_bucket = google_storage_bucket.bucket.name
  source_archive_object = google_storage_bucket_object.set-mig-code.name
  trigger_http          = true
  timeout               = 60
  entry_point           = "Main"

  depends_on = [google_storage_bucket_object.set-mig-code]

}

# Assign permissions to allow anon invocation
resource "google_cloudfunctions_function_iam_member" "invoker" {
  project        = var.gcp-project-name
  cloud_function = google_cloudfunctions_function.set-mig-function.name
  role   = "roles/cloudfunctions.invoker"
  member = "allUsers"
}
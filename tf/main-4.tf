resource "google_project_service" "enable-cloudrun" {
  project = var.gcp-project-name
  service = "run.googleapis.com"
  disable_on_destroy = false
}

resource "google_cloud_run_service" "manual-scheduler" {
  name     = "manual-scalar-controller"
  location = var.cr-region

  template {
    spec {
      containers {
        image = var.manual-scheduler-docker-image
        env {
          name = "mig_name"
          value = var.mig-name
        }
        env {
          name = "mig_region"
          value = var.region
        }
        env { 
          name = "autoscaler_cf"
          value = google_cloudfunctions_function.autoscaler-function.https_trigger_url
        }
        env { 
          name = "mig_size_cf"
          value = google_cloudfunctions_function.set-mig-function.https_trigger_url
        }
        env { 
          name = "GCP_PROJECT"
          value = var.gcp-project-name
        }
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
  autogenerate_revision_name = true

  depends_on = [google_project_service.enable-cloudrun]

}

# Set Permissions
data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

resource "google_cloud_run_service_iam_policy" "noauth" {
  location    = google_cloud_run_service.manual-scheduler.location
  project     = google_cloud_run_service.manual-scheduler.project
  service     = google_cloud_run_service.manual-scheduler.name

  policy_data = data.google_iam_policy.noauth.policy_data
}
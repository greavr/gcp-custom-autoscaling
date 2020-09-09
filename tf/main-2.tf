## Stackdriver custom metric
resource "google_project_service" "enable-stackdriver" {
  project = var.gcp-project-name
  service = "stackdriver.googleapis.com"
}

resource "google_monitoring_metric_descriptor" "session_count" {
  description = "Current Session Status per server"
  display_name = "Current Sessions"
  type = "custom.googleapis.com/sessions/session_count"
  metric_kind = "GAUGE"
  value_type = "DOUBLE"
  unit = "{Count}"
  labels {
      key = "server_id"
      value_type = "STRING"
      description = "Server Name."
  }
  launch_stage = "BETA"
  metadata {
    sample_period = "60s"
    ingest_delay = "30s"
  }
}
# Enable Pub Sub Service
resource "google_project_service" "enable-pubsub" {
  project = var.gcp-project-name
  service = "pubsub.googleapis.com"
  disable_on_destroy = false
}

# Pub Sub Topic
resource "google_pubsub_topic" "scale-events-topic" {
  name = format("%s-scaling-events",var.mig-name)
  depends_on = [google_project_service.enable-pubsub]
}

# Pub Sub Subscription
resource "google_pubsub_subscription" "scale-events-sub" {
  name  = format("%s-scaling-events-pull-subscription",var.mig-name)
  topic = google_pubsub_topic.scale-events-topic.name

  # 20 minutes
  message_retention_duration = "1200s"
  retain_acked_messages      = true

  ack_deadline_seconds = 20

  expiration_policy {
    ttl = "300000.5s"
  }
  retry_policy {
    minimum_backoff = "10s"
  }

  enable_message_ordering    = false
}
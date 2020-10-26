## Outputs:
output "Autoscaler_Web_Address" { 
    value = google_cloudfunctions_function.autoscaler-function.https_trigger_url
}

output "Manual_Scaler_Web_Adress" { 
    value = google_cloud_run_service.manual-scheduler.status[0].url
}

output "Manual_Scaler_Docker_Image" { 
    value = var.manual-scheduler-docker-image
}

output "PubSub_Topic" {
    value = google_pubsub_topic.scale-events-topic.id
}
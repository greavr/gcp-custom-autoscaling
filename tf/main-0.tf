terraform {
  required_providers {
    google = {
      source = "hashicorp/google"
    }
  }
}

// Google Cloud provider & Beta
provider "google" {
  project = var.gcp-project-name
  region = var.region
  zone = var.zone
}
provider "google-beta" {
  project = var.gcp-project-name
}

# Create Bucket for code & Upload it
resource "google_storage_bucket" "bucket" {
  name =  format("%s%s", var.gcp-project-name, var.bucket-name)
}

# Create Zip file
data "archive_file" "session_code" {
  type        = "zip"
  output_path = "../artifacts/code.zip"
  source_dir = "../instance-code"
}

resource "google_storage_bucket_object" "code" {
  name   = "code.zip"
  bucket = google_storage_bucket.bucket.name
  source = "../artifacts/code.zip"
}

resource "google_storage_bucket_object" "bootstrap" {
  name   = "startup_script.sh"
  bucket = google_storage_bucket.bucket.name
  source = "../artifacts/startup_script.sh"
}

# Create Firewall rule
resource "google_compute_firewall" "session" {
  name    = "allow-session-check"
  network = var.gcp-vpc


  allow {
    protocol = "tcp"
    ports    = ["8080"]
  }

  source_ranges = ["0.0.0.0/0"]
   target_tags = ["session-hosts"]
}

# Create Instance template
resource "google_compute_instance_template" "default" {
  name        = "session-template"
  description = "This template is used to create sample app server instances."

  tags = ["session-hosts"]

  instance_description = "Sample Session Instance"
  machine_type         = var.instance-type
  can_ip_forward       = false

  scheduling {
    automatic_restart   = true
    on_host_maintenance = "MIGRATE"
  }

  // Create a new boot disk from an image
  disk {
    source_image = var.instance-os
    auto_delete  = true
    boot         = true
  }

  network_interface {
    network = var.gcp-vpc
    access_config {    }
  }

  metadata = {
    source_code_loc = format("gs://%s%s/code.zip", var.gcp-project-name, var.bucket-name),
    startup-script-url = format("gs://%s%s/startup_script.sh", var.gcp-project-name, var.bucket-name)
  }

  service_account {
    scopes = ["userinfo-email", "compute-ro", "storage-ro"]
  }
}

# Create Managed Instance Group
resource "google_compute_health_check" "autohealing" {
  name                = "autohealing-health-check"
  check_interval_sec  = 5
  timeout_sec         = 5
  healthy_threshold   = 2
  unhealthy_threshold = 10 # 50 seconds

  http_health_check {
    request_path = "/"
    port         = "8080"
  }
}

resource "google_compute_region_instance_group_manager" "sessions" {
  name               = var.mig-name
  version {
    instance_template  = google_compute_instance_template.default.id
  }

  base_instance_name = "session-server"
  region               = var.region
  target_size        = var.mig-size

  auto_healing_policies {
    health_check      = google_compute_health_check.autohealing.id
    initial_delay_sec = 300
  }
}
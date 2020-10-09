# GCP Project Name
variable "gcp-project-name" {
    type = string
    default = "rg-autoscaler"
}

# GCP VPC
variable "gcp-vpc" { 
    type = string
    default = "default"
}

# GCP Server Subnet
variable "gcp-serverless" {
    type = string
    default = "10.8.0.0/28"
}

# GCP VPC Connector Name
variable "vpc-connector-name" { 
    type = string
    default = "autoscaler-connector"
}

# Instance size
variable "instance-type" { 
    type = string
    default = "e2-micro"
}

# Instance Region
variable "region" { 
    type = string
    default = "us-west2"
}

# Instance Zone
variable "zone" { 
    type = string
    default = "us-west2-a"
}


# Instance OS
variable "instance-os" {
    type = string
    default = "debian-cloud/debian-9"
}

# Name of Managed Instance Group
variable "mig-name" { 
    type = string
    default = "testing-mig"
}

# Size of Managed Instance Group at start
variable "mig-size" { 
    type = number
    default = 5
}

# Used to upload code for instances & cf too
variable "bucket-name" {
    type = string
    default = "_bootstrap"
}

# Cloud Function Name
variable "cf-name" { 
    type = string
    default = "my_autoscaler"
}

# Cloud Function Max Sessions Per Box
variable "max_sessions" { 
    type = number
    default = 15
}

# Cloud Function Name
variable "min_sessions" { 
    type = number
    default = 5
}

# Cloud Function Name
variable "timeout" { 
    type = number
    default = 60
}

# Cloud Schedule timing
variable "cron-schedule" {
    type = string
    default = "*/5 * * * *"
}
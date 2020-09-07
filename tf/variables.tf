# GCP Project Name
variable "gcp-project-name" {
    type = string
    default = "prodapp1-214321"
}

# GCP VPC
variable "gcp-vpc" { 
    type = string
    default = "default"
}

# Instance size
variable "instance-type" { 
    type = string
    default = "e2-micro"
}

# Instance Region
variable "region" { 
    type = string
    default = "us-west1"
}

# Instance Zone
variable "zone" { 
    type = string
    default = "us-west1-a"
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
    default = 10
}

# Used to upload code for instances & cf too
variable "bucket-name" {
    type = string
    default = "_bootstrap"
}
# main.tf

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

# Configure the AWS Provider
provider "aws" {
  region = "us-east-2"
}

# Identidad de la cuenta — se usa para sufijar buckets S3 (globalmente unicos)
data "aws_caller_identity" "current" {}

locals {
  project       = "mlemons"
  bucket_suffix = data.aws_caller_identity.current.account_id
}

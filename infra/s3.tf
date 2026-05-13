# s3.tf
#
# Cuatro buckets del proyecto. Privados (block public access default).
# force_destroy = true porque es entorno academico; quitar en prod.

resource "aws_s3_bucket" "raw" {
  bucket        = "${local.project}-raw-${local.bucket_suffix}"
  force_destroy = true
}

resource "aws_s3_bucket" "processed" {
  bucket        = "${local.project}-processed-${local.bucket_suffix}"
  force_destroy = true
}

resource "aws_s3_bucket" "models" {
  bucket        = "${local.project}-models-${local.bucket_suffix}"
  force_destroy = true
}

resource "aws_s3_bucket" "results" {
  bucket        = "${local.project}-results-${local.bucket_suffix}"
  force_destroy = true
}

# Bloquear acceso publico en los 4 buckets (datos del proyecto son privados)
resource "aws_s3_bucket_public_access_block" "raw" {
  bucket                  = aws_s3_bucket.raw.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "processed" {
  bucket                  = aws_s3_bucket.processed.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "models" {
  bucket                  = aws_s3_bucket.models.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_public_access_block" "results" {
  bucket                  = aws_s3_bucket.results.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

output "bucket_raw" {
  value = aws_s3_bucket.raw.bucket
}

output "bucket_processed" {
  value = aws_s3_bucket.processed.bucket
}

output "bucket_models" {
  value = aws_s3_bucket.models.bucket
}

output "bucket_results" {
  value = aws_s3_bucket.results.bucket
}

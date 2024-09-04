# An S3 bucket for fieldscope to export our data to
resource "aws_s3_bucket" "echolalia_bucket" {
  bucket        = var.echolalia_bucket_name
  force_destroy = false # don't delete objects in the bucket when destroying the bucket
}

# No public access to the bucket
resource "aws_s3_bucket_public_access_block" "sound_fieldscope_public_bucket_access" {
  bucket                  = aws_s3_bucket.echolalia_bucket.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
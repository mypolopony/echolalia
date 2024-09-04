variable "project_name" {
  type        = string
  description = "The name of the project"
  default     = "echolalia"
}

variable "echolalia_bucket_name" {
  type        = string
  description = "The name of the S3 bucket that holds Echolalia resources"
  default     = "smcphers-echolalia"
}

variable "smcpherson_aws_account_id" {
  type        = string
  description = "The AWS account ID for smcpheron"
  default     = "897729117324"
}

variable "aws_region" {
  type        = string
  description = "The AWS region name"
  default     = "us-west-1"
}
output "sagemaker_role_arn" {
  value = aws_iam_role.sagemaker_role.arn
}

output "echolalia_ecr_arn" {
  value = aws_ecr_repository.echolalia_ecr_repo.arn
}
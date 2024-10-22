# The repo for storing images
resource "aws_ecr_repository" "echolalia_ecr_repo" {
  name                 = var.project_name
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = false
  }
}

# The repo for storing images
resource "aws_ecr_repository" "echolalia_chat_ecr_repo" {
  name                 = "echolalia-chat"
  image_tag_mutability = "MUTABLE"
  force_delete         = true

  image_scanning_configuration {
    scan_on_push = false
  }
}
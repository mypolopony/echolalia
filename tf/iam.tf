# Create the IAM Role with Trust Policy
resource "aws_iam_role" "application_role" {
  name = "application-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"  # If your container is running on EC2
          # If using Lambda, replace with "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

# Create a policy for S3 and Lambda permissions
resource "aws_iam_policy" "s3_lambda_policy" {
  name        = "S3LambdaAccessPolicy"
  description = "Policy to allow S3 and Lambda access"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetObject",
          "s3:PutObject",
          "lambda:InvokeFunction",
          "lambda:GetFunction"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach the policy to the IAM Role
resource "aws_iam_role_policy_attachment" "s3_lambda_policy_attachment" {
  role       = aws_iam_role.application_role.name
  policy_arn = aws_iam_policy.s3_lambda_policy.arn
}
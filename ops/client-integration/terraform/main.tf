# ==============================================================================
# Reliant AI — Triage Lambda (IaC)
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "environment" {
  type    = string
  default = "production"
}

variable "notification_routing_webhook" {
  type      = string
  sensitive = true
}

resource "aws_iam_role" "lambda_exec" {
  name = "reliant-ai-triage-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../dist"
  output_path = "${path.module}/lambda_function.zip"
}

resource "aws_lambda_function" "triage_alerting" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "reliant-ai-infrastructure-triage-${var.environment}"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "triage-alerting.handler"
  runtime          = "nodejs20.x"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  timeout          = 10
  memory_size      = 256

  environment {
    variables = {
      NODE_ENV                     = var.environment
      NOTIFICATION_ROUTING_WEBHOOK = var.notification_routing_webhook
    }
  }

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
    Project     = "ReliantAI-Ops"
  }
}

output "lambda_function_arn" {
  value       = aws_lambda_function.triage_alerting.arn
  description = "ARN of the deployed triage Lambda function."
}

output "lambda_function_name" {
  value       = aws_lambda_function.triage_alerting.function_name
  description = "Name of the deployed triage Lambda function."
}

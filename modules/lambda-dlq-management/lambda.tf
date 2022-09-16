data "archive_file" "this" {
  source_file = "${path.module}/lambda_code/lambda_dlq_management.py"
  type        = "zip"
  output_path = "${path.module}/lambda_code/lambda_dlq_management.zip"
}

resource "aws_lambda_function" "this" {
  function_name    = local.resource_id
  handler          = "lambda_dlq_management.lambda_handler"
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.9"
  memory_size      = var.lambda_memory
  timeout          = var.lambda_timeout
  filename         = data.archive_file.this.output_path
  source_code_hash = data.archive_file.this.output_base64sha256
  dead_letter_config {
    target_arn = aws_sqs_queue.this.arn
  }
  environment {
    variables = {
      ENABLE_DLQ_MANAGEMENT = false #var.enable_dlq_management
      RESOURCE_ID           = "${local.resource_id}-for-all-lambdas"
      SKIP_TAG_NAME         = var.skip_tag_name
      SKIP_TAG_NAME         = var.skip_tag_value
      SQS_QUEUE_ARN         = aws_sqs_queue.this.arn
    }
  }
  tags = {
    Description = "Lambda function for Lambda DLQ management terraform module ${local.resource_id}"
    ManagedBy   = "terraform"
  }
}

data "archive_file" "test" {
  source_file = "${path.module}/lambda_code/lambda_dlq_management-test.py"
  type        = "zip"
  output_path = "${path.module}/lambda_code/lambda_dlq_management-test.zip"
}
resource "aws_lambda_function" "test" {
  count            = 150
  function_name    = "zzz-${local.resource_id}-${count.index}"
  handler          = "lambda_dlq_management.lambda_handler"
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.9"
  memory_size      = var.lambda_memory
  timeout          = 30
  filename         = data.archive_file.test.output_path
  source_code_hash = data.archive_file.test.output_base64sha256
  environment {
    variables = {
      ENABLE_DLQ_MANAGEMENT = false #var.enable_dlq_management
      RESOURCE_ID           = "TEST"
      SKIP_TAG_NAME         = "TEST"
      SKIP_TAG_NAME         = "TEST"
      SQS_QUEUE_ARN         = "TEST"
    }
  }
  tags = {
    Description = "TEST"
  }
  lifecycle {
    ignore_changes = [
      tags, dead_letter_config,
    ]
  }
}
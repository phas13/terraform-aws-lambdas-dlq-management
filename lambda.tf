data "archive_file" "this" {
  source_file = "${path.module}/lambda_code/lambda_dlq_management.py"
  type        = "zip"
  output_path = "${path.module}/lambda_code/lambda_dlq_management.zip"
}

resource "aws_lambda_function" "this" {
  function_name    = "${local.project}-${data.aws_region.current.name}"
  handler          = "lambda_dlq_management.lambda_handler"
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.9"
  memory_size      = var.lambda_memory
  timeout          = var.lambda_timeout
  filename         = data.archive_file.this.output_path
  source_code_hash = data.archive_file.this.output_base64sha256
  environment {
    variables = {
      PROJECT        = local.project
      SKIP_TAG_NAME  = "ManagedBy"
      SKIP_TAG_VALUE = "terraform"
      SQS_QUEUE      = aws_sqs_queue.this.arn
    }
  }
  tags = {
    Description = "Lambda function for Lambda DLQ management terraform module"
    ManagedBy   = "terraform"
  }
}

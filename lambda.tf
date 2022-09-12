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
      PROJECT        = "${local.project}-${data.aws_region.current.name}"
      SKIP_TAG_NAME  = "ManagedBy"
      SKIP_TAG_VALUE = "terraform"
      SQS_QUEUE_ARN  = aws_sqs_queue.this.arn
    }
  }
  tags = {
    Description = "Lambda function for Lambda DLQ management terraform module"
    ManagedBy   = "terraform"
  }
}

resource "aws_lambda_function" "test" {
  count = 10
  function_name    = "${local.project}-${data.aws_region.current.name}-count-${count.index}"
  handler          = "lambda_dlq_management.lambda_handler"
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.9"
  memory_size      = var.lambda_memory
  timeout          = var.lambda_timeout
  filename         = data.archive_file.this.output_path
  source_code_hash = data.archive_file.this.output_base64sha256
  environment {
    variables = {
      PROJECT        = "TEST"
      SKIP_TAG_NAME  = "TEST"
      SKIP_TAG_VALUE = "TEST"
      SQS_QUEUE_ARN  = aws_sqs_queue.this.arn
    }
  }
  tags = {
    Description = "TEST"
    ManagedBy   = "TEST"
  }
}
resource "aws_cloudwatch_log_group" "this" {
  name = "/aws/lambda/${aws_lambda_function.this.function_name}"
  tags = {
    Description = "CloudWatch LogGroup for Lambda DLQ management terraform module"
  }
}

resource "aws_cloudwatch_event_rule" "this" {
  name                = aws_lambda_function.this.function_name
  description         = "CloudWatch Event Rule for Lambda DLQ management terraform module"
  schedule_expression = var.invocation_rate
}

resource "aws_cloudwatch_event_target" "this" {
  rule      = aws_cloudwatch_event_rule.this.name
  target_id = "lambda"
  arn       = aws_lambda_function.this.arn
}

resource "aws_lambda_permission" "this" {
  statement_id  = "AllowExecutionFromCloudWatch-${aws_lambda_function.this.function_name}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.this.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.this.arn
}

locals {
  # project - name of management lambda function and 
  project = "terraform-aws-lambda-dlq-management"
}

variable "invocation_rate" {
  type        = string
  default     = "rate(1 day)"
  description = "The rate at which the lambda will be triggered. Must be a string with rate() format"

  validation {
    condition     = can(regex("(^rate(\\([^)]+\\)))|(^cron(\\([^)]+\\)))", var.invocation_rate))
    error_message = "Please use an AWS rate() or cron() cron object for the invocation_rate https://docs.aws.amazon.com/lambda/latest/dg/services-cloudwatchevents-expressions.html."
  }
}

variable "lambda_memory" {
  type        = number
  default     = 128
  description = "Amount of memory, in MB, to allocate to the Lambda function that will enforce the CloudWatch Log configuration. Increase if receiving timeout errors."
}

variable "lambda_timeout" {
  type        = number
  default     = 30
  description = "Amount of time, in seconds, for the Lambda function timeout. Increase if receiving timeout errors."
}

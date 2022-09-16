data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  resource_id = "${var.module_id}-${data.aws_region.current.name}"
}

variable "enable_dlq_management" {
  type    = bool
  default = true
}

variable "module_id" {
  type        = string
  default     = "terraform-aws-lambda-dlq-management"
  description = "Name that will be applied to most resources created by module, + region"
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
  default     = 180
  description = "Amount of time, in seconds, for the Lambda function timeout. Increase if receiving timeout errors."
}

variable "skip_tag_name" {
  type        = string
  default     = "ManagedBy"
  description = "Tag that should be skipped by automation module"
}

variable "skip_tag_value" {
  type        = string
  default     = "terraform"
  description = "Tag value that should be skipped by automation module"
}
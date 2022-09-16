data "aws_iam_policy_document" "sqs" {
  statement {
    sid    = "LambdaManagement"
    effect = "Allow"
    actions = [
      "sqs:SendMessage"
    ]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      variable = "aws:RequestTag/DLQAutomationMarker"
      values   = ["${local.resource_id}"]
    }
  }
}

resource "aws_sqs_queue" "this" {
  name   = local.resource_id
  policy = data.aws_iam_policy_document.sqs.json
  tags = {
    Description = "SQS queue for all lambdas managed by ${local.resource_id}"
    ManagedBy   = "terraform"
  }
}

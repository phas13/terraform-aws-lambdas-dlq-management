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
      values   = ["${local.project}"]
    }
  }
}

resource "aws_sqs_queue" "terraform_queue" {
  name   = "${local.project}-${data.aws_region.current.name}"
  policy = data.aws_iam_policy_document.sqs.json
  tags = {
    Description = "DLQ for all lambdas managed by ${local.project}"
  }
}

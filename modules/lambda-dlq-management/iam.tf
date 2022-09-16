#
# IaM Configuration for management lambda finction
#
resource "aws_iam_role" "lambda" {
  name               = local.resource_id
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
  tags = {
    Description = "Role for Lambda DLQ management terraform module ${local.resource_id}"
    ManagedBy   = "terraform"
  }
}

data "aws_iam_policy_document" "lambda" {
  statement {
    sid = "LambdaManagement"
    actions = [
      "lambda:GetFunctionConfiguration",
      "lambda:ListFunctions",
      "lambda:ListTags",
      "lambda:TagResource",
      "lambda:UntagResource",
      "lambda:UpdateFunctionConfiguration"
    ]
    resources = [
      "*"
    ]
    effect = "Allow"
  }
  statement {
    sid = "IaMCreatePolicy"
    actions = [
      "iam:CreatePolicy",
      "iam:GetPolicy",
      "iam:AttachRolePolicy",
      "iam:DetachRolePolicy",
      "iam:DeletePolicy"
    ]
    resources = [
      "*"
    ]
    effect = "Allow"
  }
  statement {
    sid       = "SQSUsage"
    actions   = ["sqs:SendMessage"]
    resources = ["${aws_sqs_queue.this.arn}"]
    effect    = "Allow"
  }
  statement {
    sid = "SelfLoggingAccess"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = [
      "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${local.resource_id}:log-stream:*",
      "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${local.resource_id}"
    ]
  }
}

resource "aws_iam_policy" "lambda" {
  name        = local.resource_id
  description = "Policy for Lambda DLQ management terraform module ${local.resource_id}"
  policy      = data.aws_iam_policy_document.lambda.json
}

resource "aws_iam_role_policy_attachment" "lambda" {
  role       = aws_iam_role.lambda.name
  policy_arn = aws_iam_policy.lambda.arn
}

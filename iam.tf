resource "aws_iam_role" "this" {
  name               = "${local.project}-lambda-role"
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
    Description = "Role for Lambda DLQ management terraform module"
  }
}

data "aws_iam_policy_document" "this" {
  statement {
    sid = "LambdaManagement"
    actions = [
      "lambda:ListFunctions",
      "lambda:UpdateFunctionConfiguration"
    ]
    resources = [
      "*"
    ]
    effect = "Allow"
  }
  statement {
    sid = "SelfLoggingAccess"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = [
      "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${local.project}-${data.aws_region.current.name}:log-stream:*",
      "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/lambda/${local.project}-${data.aws_region.current.name}"
    ]
  }
}

resource "aws_iam_policy" "this" {
  name        = "${local.project}-lambda-policy"
  description = "Policy for Lambda DLQ management terraform module"
  policy      = data.aws_iam_policy_document.this.json
}

resource "aws_iam_role_policy_attachment" "this" {
  role       = aws_iam_role.this.name
  policy_arn = aws_iam_policy.this.arn
}

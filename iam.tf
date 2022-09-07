resource "aws_iam_role" "this" {
  name = "${local.project}-lambda-role"
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
      "lambda:List*",
      "lambda:Get*",
      "lambda:UpdateFunctionConfiguration"
    ]
    resources = [
      "arn:aws:lambda:${data.aws_region.current}:${data.aws_caller_identity.current}:function:*"
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
      "arn:aws:logs:${data.aws_region.current}:${data.aws_caller_identity.current}:log-group:/aws/lambda/${local.project}-${data.aws_region.current}:log-stream:*",
      "arn:aws:logs:${data.aws_region.current}:${data.aws_caller_identity.current}:log-group:/aws/lambda/${local.project}-${data.aws_region.current}"
    ]
  }
}

resource "aws_iam_policy" "this" {
  name   = "${local.project}-lambda-policy"
  description = "Policy for Lambda DLQ management terraform module"
  policy = data.aws_iam_policy_document.this.json
}

# Attach the above IAM policy to the IAM role
resource "aws_iam_role_policy_attachment" "this" {
  role       = aws_iam_role.this.name
  policy_arn = aws_iam_policy.log-management-lambda-policy.arn
}

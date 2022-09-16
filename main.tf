resource "random_string" "this" {
  length  = 16
  special = false
  upper   = false
  numeric = false
}

module "lambda_dlq_management_automation" {
  source    = "./modules/lambda-dlq-management"
  module_id = "lambda-dlq-management-${random_string.this.result}"
}

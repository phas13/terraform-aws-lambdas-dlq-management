# What this all about

Central management of Lambdas DLQ.

This module creates lambda management function that automatically manage all lambda functions dead letter queues in such way:

* we create single SQS queue for all lambda functions via terraform
* we create policy with access to this queue via management lambda function
* if lambda function already has DLQ, it will be skipped by management lambda.
* if lambda function has tag reflected in SKIP_TAG_NAME/SKIP_TAG_NAME function variables, it will be skipped by management lambda. It allow us to skip finctions managed by terraform, for instance, but in this case DLQ should be configurted via terraform.
* if function has not DLQ and tag, then management lambda function will:
  * attach policy with DLQ access to lambda function role
  * add DLQ configuration to lambda function
  * add DLQAutomationMarker tag to lambda function with name of management lambda function in value


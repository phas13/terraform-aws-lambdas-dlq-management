import boto3
import os
import traceback
import json

def lambda_handler(event, context):
    lm = boto3.client("lambda")
    iam = boto3.client("iam")
    print(f">>> Processing Lambda functions in region {lm.meta.region_name} <<<")
    if os.environ.get("ENABLE_DLQ_MANAGEMENT") == "true":
        print("-- SETUP DLQ FOR LAMBDA FUNCTIONS ---")
    else:
        print("-- REMOVE DLQ FOR LAMBDA FUNCTIONS ---")
    policyName = str(os.environ.get("RESOURCE_ID"))
    awsAccountId = str(boto3.client('sts').get_caller_identity()['Account'])
    policyARN = "arn:aws:iam::"+awsAccountId+":policy/"+policyName

    if os.environ.get("ENABLE_DLQ_MANAGEMENT") == "true":
        # Prepare policy for lambdas to access SQS queue.
        # If policy exist - we use existing, if not exist - we create
        print (f"> Create/Modify IaM Policy with lambda access to SQS Queue")
        sqs_lambdas_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "sqs:SendMessage",
                    "Resource": os.environ.get("SQS_QUEUE_ARN")
                }
            ]
        }
        try:
          print("Check if policy" + policyARN + " exist:")
          responseGetPolicy = iam.get_policy(
              PolicyArn=policyARN
          )
          print(responseGetPolicy)
        except:
            print("Policy " + policyARN + " does not exist, goint to create")
            responsePolicy = iam.create_policy(
              PolicyName=policyName,
              Description='Allow Lambdas managed by module to send messages to SQS queue',
              PolicyDocument=json.dumps(sqs_lambdas_policy)
            )
            print(responsePolicy)

    fnumber = 0 # functions counter
    paginator = lm.get_paginator('list_functions')
    for response in paginator.paginate():
        for lambdafunction in response['Functions']:
            # Processing all lambda functions in region one by one
            # Skip finction if:
            # * DLQ configuration exist
            # * managed by other tool specified by SKIP_TAG_NAME/SKIP_TAG_VALUE
            fnumber = fnumber + 1
            print(f">> Processing function {fnumber}: {lambdafunction['FunctionName']}:")
            try:

                # Set modification markers
                marker_dlq = 0 # 0 - lambda has DLQ config, 1 - lambda has no DLQ config
                marker_managed = 0 # 0 - lambda is not managed, 1 - lambda managed by other tool that will provide DLQ config
                marker_remove_dlq = 0 # 0 - leave DLQ configuration as is, 1 - remove DLQ configuration
                
                roleName = lambdafunction['Role'].split('/',1)[1]
                
                print(f"* Function Name: {lambdafunction['FunctionName']}")
                print(f"* Function ARN: {lambdafunction['FunctionArn']}")
                print(f"* Role ARN: {lambdafunction['Role']}")
                try:
                    print(f"* DeadLetterConfig: {lambdafunction['DeadLetterConfig']}")
                    marker_dlq = 1
                except:
                    print (f"* DeadLetterConfig: NOT CONFIGURED")
                
                responseListTags = lm.list_tags(
                    Resource=lambdafunction['FunctionArn']
                )
                
                for (t, v) in (responseListTags['Tags'].items()):
                    if t == os.environ.get("SKIP_TAG_NAME") and v == os.environ.get("SKIP_TAG_VALUE"):
                        print("* " + str(os.environ.get("SKIP_TAG_NAME")) + ": " + str(os.environ.get("SKIP_TAG_VALUE")))
                        marker_managed = 1
                    if t == "DLQAutomationMarker" and v == str(os.environ['RESOURCE_ID']):
                        print("* DLQAutomationMarker: " + str(os.environ.get("RESOURCE_ID")))
                        marker_remove_dlq = 1
                
                if os.environ.get("ENABLE_DLQ_MANAGEMENT") == "true":
                    if marker_dlq == 0 and marker_managed == 0:
                        print(f"Add policy {policyARN} to role {lambdafunction['Role']}...")
                        responseAddPolicyToRole = iam.attach_role_policy(
                            RoleName=roleName,
                            PolicyArn=policyARN
                        )
                        print(responseAddPolicyToRole)
                        print(f"Add DeadLetterConfig...")
                        responseAddDeadLetterConfig = lm.update_function_configuration(
                            FunctionName=lambdafunction['FunctionName'],
                            DeadLetterConfig={
                                'TargetArn': os.environ.get("SQS_QUEUE_ARN")
                            }
                        )
                        print(responseAddDeadLetterConfig)
                        print(f"Add/renew Tag DLQAutomationMarker...")
                        responseAddTag = lm.tag_resource(
                            Resource=lambdafunction['FunctionArn'],
                            Tags={
                                "DLQAutomationMarker": "{}".format(str(os.environ['RESOURCE_ID']))
                            }
                        )
                        print(responseAddTag)
                    else:
                        print(f"We skip this function because it has DLQ config or managed by other tool that should provide DLQ config")
                else:
                    if marker_remove_dlq == 1 and marker_managed == 0:
                        try:
                            print(f"Remove DeadLetterConfig...")
                            responseRemoveDeadLetterConfig = lm.update_function_configuration(
                                FunctionName=lambdafunction['FunctionName'],
                                DeadLetterConfig={
                                    'TargetArn': ''
                                }
                            )
                            print(responseRemoveDeadLetterConfig)
                        except:
                            print((f"ERROR Removing DeadLetterConfig"))
                        try:
                            print(f"Remove policy {policyARN} from role {lambdafunction['Role']}")
                            responseDetachPolicyFromRole = iam.detach_role_policy(
                                RoleName=roleName,
                                PolicyArn=policyARN
                            )
                            print(responseDetachPolicyFromRole)
                        except:
                            print((f"Policy is not attached or does not exist"))
                        print(f"Remove Tag DLQAutomationMarker...")
                        responseRemoveTag = lm.untag_resource(
                            Resource=lambdafunction['FunctionArn'],
                            TagKeys=[
                                "DLQAutomationMarker",
                            ]
                        )
                        print(responseRemoveTag)
                
            except Exception as e:
                print(f"Ran into error when processing function {lambdafunction['FunctionName']}")
                print(traceback.format_exc())
    
    print(f">>> Done configuring lambda functions for {lm.meta.region_name} <<<")

    if os.environ.get("ENABLE_DLQ_MANAGEMENT") == "false":
        # Remove policy for lambdas to access SQS queue.
        print (f">> Remove IaM Policy with lambda access to SQS Queue")
        try:
          print("Check if policy" + policyARN + " exist:")
          responseDeletePolicy = iam.delete_policy(
              PolicyArn=policyARN
          )
          print(responseDeletePolicy)
        except:
            print("Policy " + policyARN + " does not exist, or can not be deleted")

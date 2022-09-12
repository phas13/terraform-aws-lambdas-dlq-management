import boto3
import os
import traceback
import json

def retrieve_lambdas(lm):
    lambdas_response = lm.list_functions()
    try:
        region_lambdas = lambdas_response['Functions']
    except Exception as e:
        print(f"Ran into error when retrieving Lambdas for {lm.meta.region_name} region")
        print(traceback.format_exc())
    while 'nextToken' in lambdas_response:
        lambdas_response = lm.list_functions(nextToken=lambdas_response['nextToken'])
        region_lambdas.extend(lambdas_response['Functions'])
    return region_lambdas

def configure_lambdas_dlq(lm, iam, lambdas):

    # Prepare policy for lambdas to access SQS queue.
    # If policy exist - we use existing, if not exist - we create
    print (f">> Create/Modify IaM Policy with lambda access to SQS Queue")
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
    policyName = str(os.environ.get("PROJECT"))
    awsAccountId = str(boto3.client('sts').get_caller_identity()['Account'])
    policyARN = "arn:aws:iam::"+awsAccountId+":policy/"+policyName
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

    # Processing all lambda functions in region one by one
    # Skip finction if:
    # * DLQ configuration exist
    # * managed by other tool specified by SKIP_TAG_NAME/SKIP_TAG_VALUE
    for lambdafunction in lambdas:
        try:
            print(f">> Processing function {lambdafunction['FunctionName']}:")            
            
            # Set modification markers
            marker_dlq = 0 # 0 - lambda has DLQ config, 1 - lambda has no DLQ config
            marker_managed = 0 # 0 - lambda is not managed, 1 - lambda managed by other tool that will provide DLQ config

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

            if marker_dlq == 0 and marker_managed == 0:
                print(f"Add policy {policyARN} to role {lambdafunction['Role']}")
                roleName = lambdafunction['Role'].split('/',1)[1]
                responseAddPolicyToRole = iam.attach_role_policy(
                    RoleName=roleName,
                    PolicyArn=policyARN
                )
                print(responseAddPolicyToRole)
                print(f"Add/renew TAG DLQAutomationMarker...")
                responseTagResource = lm.tag_resource(
                    Resource=lambdafunction['FunctionArn'],
                    Tags={
                        "DLQAutomationMarker": "{}".format(str(os.environ['PROJECT']))
                    }
                )
                print(responseTagResource)
                print(f"Add DeadLetterConfig...")
                responseDeadLetterConfig = lm.update_function_configuration(
                    FunctionName=lambdafunction['FunctionName'],
                    DeadLetterConfig={
                        'TargetArn': os.environ.get("SQS_QUEUE_ARN")
                    }
                )
                print(responseDeadLetterConfig)
            else:
                print(f"We skip this function because it has DLQ config or managed by other tool that should provide DLQ config")
            
        except Exception as e:
            print(f"Ran into error when processing function {lambdafunction['FunctionName']}")
            print(traceback.format_exc())
    print(f">>> Done configuring lambda functions for {lm.meta.region_name} <<<")
    print(f"")

def lambda_handler(event, context):
    lm = boto3.client("lambda")
    iam = boto3.client("iam")
    print(os.environ.get("ENABLE_DLQ_MANAGEMENT"))
    if os.environ.get("ENABLE_DLQ_MANAGEMENT") == "true":
        print("   SETUP DLQ FOR LAMBDA FUNCTIONS")
    else:
        print("   REMOVE DLQ FOR LAMBDA FUNCTIONS")
    print(f">>> Processing Lambda functions in region {lm.meta.region_name} <<<")
    configure_lambdas_dlq(lm, iam, retrieve_lambdas(lm))
    return True

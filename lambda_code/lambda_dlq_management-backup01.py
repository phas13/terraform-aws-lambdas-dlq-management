import boto3
import os
import traceback

# If lambda have TAG ManagedBy = terraform, then skip, DLQ configuration in terraform
# If lambda have DLQ configuration and have no TAG DLQAutomationMarker, then skip, DLQ configuration done by someone else
# If lambda pass requirements and should have DLQ only for pass security conpliance, then add DLQ configuration. All lambdas will sent messages in single SQS queue

def retrieve_lambdas(lm):
    # """
    # Retrieve all Lambda function  in a region
    # :param lm: Lambda boto3 client object
    # :return: region_lambdas as a list of dicts containing lambda names
    # """
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

def configure_lambdas_dlq(lm, lambdas):
    for lambdafunction in lambdas:
        try:
            print(f">> Processing function {lambdafunction['FunctionName']}:")            
            
            # Set modification markers
            marker_dlq = 0 # 0 - lambda has DLQ config, 1 - lambda has no DLQ config
            marker_managed = 0 # 0 - lambda is not managed, 1 - lambda managed by other tool that will provide DLQ config

            # responseConfig = lm.get_function_configuration(
            #     FunctionName=lambdafunction['FunctionName']
            # )
            print(f"* Function Name: {lambdafunction['FunctionName']}")
            print(f"* Function ARN: {lambdafunction['FunctionArn']}")
            print(f"* Role ARN: {lambdafunction['Role']}")
            try:
                print(f"* DeadLetterConfig: {lambdafunction['DeadLetterConfig']}")
                marker_dlq = 1
            except:
                print (f"* DeadLetterConfig: NOT CONFIGURED")
            # print(f"*** Full response: {responseConfig}")

            responseListTags = lm.list_tags(
                Resource=lambdafunction['FunctionArn']
            )
            # print(responseListTags['Tags'])
            for (t, v) in (responseListTags['Tags'].items()):
                # print(t)
                # print(v)
                if t == os.environ.get("SKIP_TAG_NAME") and v == os.environ.get("SKIP_TAG_VALUE"):
                    print("* " + str({os.environ.get("SKIP_TAG_NAME")}) + ": " + str({os.environ.get("SKIP_TAG_VALUE")}))
                    marker_managed = 1

            if marker_dlq == 0 and marker_managed == 0:
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
            
            # Add DLQAutomationMarker Tag
            # DLQAutomationMarker=str(os.environ['PROJECT'])
            # responseTagResource = lm.tag_resource(
            #     Resource=lambdafunction['FunctionArn'],
            #     Tags={
            #         "DLQAutomationMarker": "{}".format(DLQAutomationMarker)
            #     }
            # )
            # print(responseTagResource)
        except Exception as e:
            print(f"Ran into error when processing function {lambdafunction['FunctionName']}")
            print(traceback.format_exc())
    print(f">>> Done configuring lambda functions for {lm.meta.region_name} <<<")
    print(f"")

def lambda_handler(event, context):
    # print(">>> START EXECUTION <<<")

    # print(">>> Instantiate Lambda client in current region <<<")
    lm = boto3.client("lambda")

    # retrieve_lambdas(lm)
    # lmoutput = retrieve_lambdas(lm)
    # print(f'{lmoutput}')

    print(f">>> Processing Lambda functions in region {lm.meta.region_name} <<<")
    configure_lambdas_dlq(lm, retrieve_lambdas(lm))

    # print(">>> END EXECUTION <<<")
    return True

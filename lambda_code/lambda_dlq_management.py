import boto3
import os
import traceback

def retrieve_lambdas(lm):
    """
    Retrieve all Lambda function  in a region
    :param lm: Lambda boto3 client object
    :return: region_lambdas as a list of dicts containing lambda names
    """
    lambdas_response = lm.list_functions()
    try:
        region_lambdas = lambdas_response['Functions']
    except Exception as e:
        print(f"Ran into error when retrieving Lambdas for {lm.meta.region_name} region")
        print(traceback.format_exc())
    while 'nextToken' in lambdas_response:
        lambdas_response = lm.list_functions(nextToken=lambdas_response['nextToken'])
        region_lambdas.extend(lambdas_response['Functions'])
    return lambdas_response

def configure_lambdas_dlq(lm, lambdas):
    for lambdafunction in lambdas:
        try:
            response = lm.tag_resource(
                Resource=lambdafunction['FunctionArn'],
                Tags={
                    'DEPARTMENT': 'Department A'
                }
            )
            print(response)
        except Exception as e:
            print(f"Ran into error when TAGging function {lambdafunction['FunctionName']}")
            print(traceback.format_exc())
    print(f">>> Done configuring function for {lm.meta.region_name} <<<")

def lambda_handler(event, context):
    print(">>> START EXECUTION <<<")

    print(">>> Instantiate Lambda client in current region <<<")
    lm = boto3.client("lambda")

    retrieve_lambdas(lm)
    lmoutput = retrieve_lambdas(lm)
    print(f'{lmoutput}')

    configure_lambdas_dlq(lm, retrieve_lambdas(lm))

    print(">>> END EXECUTION <<<")
    return True

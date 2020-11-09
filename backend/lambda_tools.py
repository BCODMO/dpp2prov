import json

import os

from dpp2prov.configuration import get_environment, get_dpp2prov_bucket_name, ENVIRONMENT_VARIABLE_NAME, BUCKET_VARIABLE_NAME
from dpp2prov.dpp2prov_logging import setup_logging


def lambda_handler():
    """
    AWS lambda handler handler. A wrapper with standard boilerplate implementing the
    best practices we've developed
    Returns:
        The wrapped lambda function or JSON response function when an error occurs.  When called,
        this wrapped function will return the appropriate output
    """
    logger = setup_logging(__name__)

    def aws_lambda_response(*args, msg_type='error', msg=None, code=500, **kwargs):
        return generate_response(code, json.dumps({msg_type: msg or 'internal'}))

    def func_wrapper(lambda_func):
        def aws_lambda_wrapper(event, context):
            if os.environ.get('PAUSE'):
                logger.warning('Function paused')
                return aws_lambda_response(event, context, msg_type='info', msg='paused', code=503)

            if not get_environment():
                logger.error(
                    f'{ENVIRONMENT_VARIABLE_NAME} environment variable missing cannot continue')
                return aws_lambda_response(event, context, msg_type='info', msg='paused', code=503)
            
            if not get_dpp2prov_bucket_name():
                logger.error(
                    f'{BUCKET_VARIABLE_NAME} environment variable missing cannot continue')
                return aws_lambda_response(event, context, msg_type='info', msg='paused', code=503)

            logger.info(f"lambda_handler.{lambda_func.__name__}")
            logger.debug(event)

        return aws_lambda_wrapper

    return func_wrapper


def generate_response(status_code=None, body='') -> object:
    """
    Generate a well formatted HTTP response object for AWS Lambda functions called by the
    API Gateway
    Args:
        status_code (int): HTTP status code to return
        body (str): Response message
    Returns:
        object
    """
    status_code = status_code or 200

    response = {
        "statusCode": status_code,
        "body": body
    }

    return response


def get_argument_value(event, argument_name):
    """
    >>> get_argument_value({'context': {'arguments': {'latitude': '42.3751'}}}, 'latitude')
    '42.3751'
    >>> get_argument_value({'context': {'arguments': {'latitude': '42.3751'}}}, 'flargyyyy')
    """
    return event['context']['arguments'].get(argument_name)


def create_200_response(message):
    headers = {
        # Required for CORS support to work
        'Access-Control-Allow-Origin': '*',
        # Required for cookies, authorization headers with HTTPS
        'Access-Control-Allow-Credentials': True,
    }
    return create_aws_lambda_response(200, {'message': message}, headers)


def create_401_response():
    headers = {
        # Required for CORS support to work
        'Access-Control-Allow-Origin': '*',
        # Required for cookies, authorization headers with HTTPS
        'Access-Control-Allow-Credentials': True,
    }
    return create_aws_lambda_response(401, 'Bleh Unauthorized', headers)


def create_aws_lambda_response(status_code, message, headers):
    return {
        'statusCode': status_code,
        'headers': headers,
        'body': json.dumps(message)
    }

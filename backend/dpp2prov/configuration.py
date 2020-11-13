import os

ENVIRONMENT_VARIABLE_NAME = 'ENVIRONMENT'
BUCKET_VARIABLE_NAME = 'BUCKET'
BUCKET_REGION_VARIABLE_NAME = 'BUCKET_REGION'
BCODMO_OFFICE_URI_VARIABLE_NAME = 'BCODMOOFFICEURI'

def get_environment():
    return os.getenv(ENVIRONMENT_VARIABLE_NAME)

def get_pipelines_bucket():
    return {'bucket': os.getenv(BUCKET_VARIABLE_NAME), 'region': os.getenv(BUCKET_REGION_VARIABLE_NAME) }

def get_bcodmo_office_uri():
    return os.getenv(BCODMO_OFFICE_URI_VARIABLE_NAME)

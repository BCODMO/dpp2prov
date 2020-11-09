import os

ENVIRONMENT_VARIABLE_NAME = 'ENVIRONMENT'
BUCKET_VARIABLE_NAME = 'BUCKET'

def get_environment():
    return os.getenv(ENVIRONMENT_VARIABLE_NAME)

def get_dpp2prov_bucket_name():
    return return os.getenv(BUCKET_VARIABLE_NAME)

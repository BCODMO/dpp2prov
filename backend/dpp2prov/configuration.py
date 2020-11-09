import os

ENVIRONMENT_VARIABLE_NAME = 'ENVIRONMENT'
BUCKET_VARIABLE_NAME = 'BUCKET'
BCODMO_OFFICE_URI_VARIABLE_NAME = 'BCODMOOFFICEURI'

def get_environment():
    return os.getenv(ENVIRONMENT_VARIABLE_NAME)

def get_dpp2prov_bucket_name():
    return return os.getenv(BUCKET_VARIABLE_NAME)

def get_bcodmo_office_uri():
    return return os.getenv(BCODMO_OFFICE_URI_VARIABLE_NAME)

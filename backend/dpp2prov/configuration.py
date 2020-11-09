import os

ENVIRONMENT_VARIABLE_NAME = 'ENVIRONMENT'
BUCKET_VARIABLE_NAME = 'BUCKET'

# {ENVIRONMENT}_{BUCKET} = the bucket to looks for FDP DPP YAML files
def get_dpp2prov_bucket_name(environment=None):
    return return os.getenv(os.getenv(ENVIRONMENT_VARIABLE_NAME) + '_' + BUCKET_VARIABLE_NAME)

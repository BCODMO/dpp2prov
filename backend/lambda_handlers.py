from pyfaaster.aws.handlers_decorators import parameters
from dpp2prov.handler_decorators import http_response
from dpp2prov.dpp_to_prov import generate_prov
from dpp2prov.dpp2prov_logging import setup_logging

logger = setup_logging(__name__)

@parameters(required_querystring=['dataset_id', 'version_id'], optional_querystring=['rdf_format'])
@http_response(default_error_message='Failed to handle something.')
def to_prov(event, context, dataset_id, version_id, rdf_format=None):
    """
    """
    return {'body': {'format': rdf_format, 'prov': generate_prov(dataset_id, version_id, rdf_format=rdf_format)} }

from pyfaaster.aws.handlers_decorators import parameters, http_response

from dpp2prov.dpp2prov import to_prov
from dpp2prov.dpp2prov_logging import setup_logging

logger = setup_logging(__name__)


@parameters(required_querystring=['dataset_id', 'version_id'], optional_querystring=['rdf_format'])
@http_response(default_error_message='Failed to handle something.')
def to_prov(event, context, dataset_id, version_id, rdf_format=None):
    """
    """
    return {'body': {'id': to_prov(dataset_id, version_id, rdf_format)} }

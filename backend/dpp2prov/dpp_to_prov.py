from datetime import datetime
from random import randrange

from hashids import Hashids
from idgenerator.idgenerator_logging import setup_logging

logger = setup_logging(__name__)


def create_id(bcodmo_version=None, content_type=None, content_id=None):
    logger.info(f'Got version, type and id: {bcodmo_version}:{content_type}:{content_id}')
    if all([bcodmo_version, content_type, content_id]):
        logger.info(f'Creating Drupal ID')
        return generate_drupal_id(bcodmo_version, content_type, content_id)
    else:
        logger.info(f'Generating a fresh ID')
        return generate_fresh_id()


def generate_drupal_id(bcodmo_version, content_type, content_id):
    """
    >>> generate_drupal_id(1, 2, 3)
    'o2fXhV'
    """
    hashids = Hashids()
    try:
        id = hashids.encode(int(bcodmo_version), int(content_type), int(content_id))
    except ValueError:
        return 'Could not generate hash id, input might not be integers'
    return id


def generate_fresh_id():
    hashids = Hashids()
    unix_timestamp = datetime.now().timestamp()
    integer_timestamp = int(unix_timestamp * 1000000)
    salt = randrange(1000000)
    id = hashids.encode(integer_timestamp, salt)
    return id

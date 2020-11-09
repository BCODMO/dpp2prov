
import logging

import os

import sys


def get_log_level():
    return os.getenv('LOG_LEVEL')


def setup_logging(name="DEFAULT_LOGGER", level='INFO'):
    """
    Helper to set up logging consistently across all lambda functions.
    Configures both a named logger and the root logger.
    Args:
        name: (str) - the name of the logger that will be configured along with the root logger
        level: (str) - The log level to use.  Default is INFO.
    Returns:
        Object: Logger object
    """
    __LAMBDA_FORMAT__ = (
        '%(aws_request_id)s\t'
        '[%(levelname)s]\t%(message)s\n'
    )
    __STANDARD_FORMAT__ = (
        '%(asctime)s.%(msecs)-3d (Z)\t%(name)s\t'
        '[%(levelname)s]\t%(message)s'
    )
    #
    __DATE_FORMAT__ = '%Y-%m-%d %H:%M:%S'
    __NAME__ = name or os.environ.get('CONFIG') or name

    logger = logging.getLogger(__NAME__)
    if running_in_aws():
        for hand in [h for h in logger.handlers]:
            hand.setFormatter(logging.Formatter(__LAMBDA_FORMAT__, datefmt=__DATE_FORMAT__))
    else:
        for h in logger.handlers:
            logger.removeHandler(h)
        h = logging.StreamHandler(sys.stdout)
        logger.addHandler(h)
        for hand in [h for h in logger.handlers]:
            hand.setFormatter(logging.Formatter(__STANDARD_FORMAT__, datefmt=__DATE_FORMAT__))
    log_level = os.environ.get('LOG_LEVEL', level)
    logger.setLevel(logging.getLevelName(log_level))
    return logger


def running_in_aws():
    return bool(os.environ.get('AWS_EXECUTION_ENV'))

#!/usr/bin/env python3

# Author::    Justin Flannery  [mailto:juftin@juftin.com]

"""
Splitwise Configuration.
"""

import logging
from os import environ
from typing import Dict

from dotenv import load_dotenv
from numpy import bool_, datetime64, float64, int64, object_

from .file_config import DOT_ENV_FILE_PATH

load_dotenv(DOT_ENV_FILE_PATH, override=True)
logger = logging.getLogger(__name__)


class SplitwiseConfig(object):
    """
    Splitwise Configuration Object
    """
    SPLITWISE_CONSUMER_KEY = environ["SPLITWISE_CONSUMER_KEY"]
    SPLITWISE_CONSUMER_SECRET = environ["SPLITWISE_CONSUMER_SECRET"]
    SPLITWISE_OAUTH_TOKEN = environ["SPLITWISE_OAUTH_TOKEN"]
    SPLITWISE_OAUTH_SECRET = environ["SPLITWISE_OAUTH_SECRET"]
    SPLITWISE_ACCESS_TOKEN = {"oauth_token": SPLITWISE_OAUTH_TOKEN,
                              "oauth_token_secret": SPLITWISE_OAUTH_SECRET}
    SPLITWISE_FINANCIAL_PARTNER = int(environ["SPLITWISE_FINANCIAL_PARTNER"])

    DTYPE_MAPPING: Dict[str, object] = {'id': int64,
                                        'transaction_balance': float64,
                                        'category': object_,
                                        'cost': float64,
                                        'created_at': datetime64,
                                        'created_by': int64,
                                        'currency': object_,
                                        'date': datetime64,
                                        'deleted': bool_,
                                        'deleted_at': datetime64,
                                        'description': object_,
                                        'payment': bool_,
                                        'updated_at': datetime64}

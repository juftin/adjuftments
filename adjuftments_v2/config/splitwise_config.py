#!/usr/bin/env python3

# Author::    Justin Flannery  [mailto:juftin@juftin.com]

"""
Splitwise Configuration.
"""

import logging
from os import environ, path
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv
from numpy import bool_, datetime64, float64, int64, object_

config_dir = Path(path.abspath(__file__)).parent
env_file = path.join(config_dir.parent.parent, '.env')
load_dotenv(env_file, override=True)

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
    SPLITWISE_SIGNIFICANT_OTHER = int(environ["SPLITWISE_SIGNIFICANT_OTHER"])

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

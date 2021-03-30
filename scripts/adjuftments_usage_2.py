#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Example Run All Script
"""

import logging
from os import getenv
from pprint import pprint

from dotenv import load_dotenv

from adjuftments_v2 import Adjuftments
from adjuftments_v2.config import DOT_ENV_FILE_PATH

load_dotenv(DOT_ENV_FILE_PATH, override=True)
logging.basicConfig(format="%(asctime)s [%(levelname)8s]: %(message)s [%(name)s]",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)
logger = logging.getLogger(__name__)

juftin = Adjuftments(endpoint="localhost",
                     api_token=getenv("DATABASE_PASSWORD"),
                     https=False, port=5000)
images = juftin._get_airtable_data(table="images")
for record in images:
    pprint(record["fields"]["Name"])

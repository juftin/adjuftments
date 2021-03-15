#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Example Run All Script
"""

import logging
from os import getenv

from adjuftments_v2.adjuftments import Adjuftments

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s [%(levelname)8s]: %(message)s [%(name)s]",
                        handlers=[logging.StreamHandler()],
                        level=logging.INFO)
    juftin = Adjuftments(endpoint="webserver",
                         api_token=getenv("DATABASE_PASSWORD"),
                         https=False, port=5000)
    juftin.prepare_database(clean_start=True)
    juftin.refresh_splitwise_data()
    juftin.refresh_airtable_expenses_data()
    juftin.refresh_dashboard()

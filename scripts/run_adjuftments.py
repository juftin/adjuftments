#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Example Run All Script
"""

import logging
from os import getenv
from time import sleep

from adjuftments_v2.adjuftments import Adjuftments
from adjuftments_v2.config import FlaskDefaultConfig

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s [%(levelname)8s]: %(message)s [%(name)s]",
                        handlers=[logging.StreamHandler()],
                        level=logging.INFO)
    juftin = Adjuftments(endpoint=FlaskDefaultConfig.API_ENDPOINT,
                         api_token=FlaskDefaultConfig.API_TOKEN,
                         https=False, port=5000)
    juftin.prepare_database(clean_start="auto")

    continue_running = True
    while continue_running is True:
        updated_splitwise_balance = juftin.refresh_splitwise_data()
        airtable_changes = juftin.refresh_airtable_expenses_data()
        if updated_splitwise_balance is not None or airtable_changes > 0:
            juftin.refresh_categories_data()
        juftin.refresh_dashboard(splitwise_balance=updated_splitwise_balance)
        sleep(30)

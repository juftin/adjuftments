#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Example Run All Script
"""
import logging

from adjuftments_v2.adjuftments import Adjuftments

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s [%(levelname)8s]: %(message)s [%(name)s]",
                        handlers=[logging.StreamHandler()],
                        level=logging.INFO)
    juftin = Adjuftments(endpoint="webserver", https=False, port=5000)
    juftin.prepare_database(clean_start=False)
    juftin.refresh_dashboard()
    juftin.refresh_splitwise_data()

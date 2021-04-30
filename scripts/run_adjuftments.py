#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Example Run All Script
"""

import logging

from requests import exceptions

from adjuftments import Adjuftments
from adjuftments.config import APIDefaultConfig
from adjuftments.job_scheduler import AdjuftmentsScheduler
from adjuftments.utils import (AdjuftmentsError, AdjuftmentsNotifications,
                               run_adjuftments_refresh_pipeline)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    console_handler = logging.StreamHandler()
    pushover_handler = AdjuftmentsNotifications(level=logging.ERROR)
    logging.basicConfig(format="%(asctime)s [%(levelname)8s]: %(message)s [%(name)s]",
                        handlers=[console_handler,
                                  pushover_handler],
                        level=logging.INFO)
    # ESTABLISH THE ADJUFTMENTS OBJECT
    adjuftments_engine = Adjuftments(endpoint=APIDefaultConfig.API_ENDPOINT,
                                     api_token=APIDefaultConfig.API_TOKEN,
                                     https=False, port=5000)
    # PREPARE THE DATABASE
    adjuftments_engine.prepare_database(clean_start="auto")
    # KICK OFF THE JOB SCHEDULER IN A BACKGROUND THREAD WITH THE ADJUFTMENTS OBJECT
    scheduler = AdjuftmentsScheduler(adjuftments=adjuftments_engine)
    scheduler.run_scheduled_events()
    # RETRY @ 10S, 30S, 1M, 5M, 10M, 30M, 60M
    sleep_configuration = [10, 30, 60, 300, 600, 1800, 3600]  # [1, 2, 3, 4, 5, 6, 7]
    # START LOGGING ERRORS @ 10M
    error_log_index = 4
    # RUN THE DATA REFRESH JOB
    run_adjuftments_refresh_pipeline(sleep_config=sleep_configuration,
                                     primary_function=adjuftments_engine.refresh_adjuftments_data,
                                     finally_function=adjuftments_engine.refresh_dashboard,
                                     error_index=error_log_index,
                                     catchable_error=(AdjuftmentsError, exceptions.ConnectionError),
                                     between_loops_sleep=20)

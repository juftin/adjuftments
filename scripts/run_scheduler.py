#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Run the Scheduler
"""

import logging

from adjuftments.job_scheduler import AdjuftmentsScheduler
from adjuftments.utils import AdjuftmentsNotifications

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    console_handler = logging.StreamHandler()
    pushover_handler = AdjuftmentsNotifications(level=logging.ERROR)
    logging.basicConfig(format="%(asctime)s [%(levelname)8s]: %(message)s [%(name)s]",
                        handlers=[console_handler,
                                  pushover_handler],
                        level=logging.INFO)
    scheduler = AdjuftmentsScheduler()
    scheduler.run_scheduled_events()

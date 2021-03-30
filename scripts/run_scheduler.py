#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Run the Scheduler
"""

import logging

from adjuftments_v2.job_scheduler import AdjuftmentsScheduler

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s [%(levelname)8s]: %(message)s [%(name)s]",
                        handlers=[logging.StreamHandler()],
                        level=logging.INFO)
    scheduler = AdjuftmentsScheduler()
    scheduler.run_scheduled_events()
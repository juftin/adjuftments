#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Scheduling Tasks for Adjuftments
"""

import logging
from os import getenv

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.combining import OrTrigger
from apscheduler.triggers.cron import CronTrigger
from dateutil.tz import tzlocal
from dotenv import load_dotenv
from pytz import timezone

from adjuftments_v2 import Adjuftments
from adjuftments_v2.config import DOT_ENV_FILE_PATH
from adjuftments_v2.config import FlaskDefaultConfig
from adjuftments_v2.plotting import AdjuftmentsPlotting

load_dotenv(DOT_ENV_FILE_PATH, override=True)
logger = logging.getLogger(__name__)


class AdjuftmentsScheduler(object):
    """
    Scheduling!
    """

    def __init__(self):
        """
        Initialize!
        """
        self.local_timezone = timezone(getenv("TZ", default=tzlocal()))
        # A LIGHTWEIGHT SCHEDULER
        self.scheduler = BlockingScheduler(
            jobstores=dict(default=MemoryJobStore()),
            executors=dict(default=ThreadPoolExecutor(max_workers=1)),
            job_defaults=dict(coalesce=False, max_instances=2),
            timezone=self.local_timezone)
        self.adjuftments = Adjuftments(endpoint=FlaskDefaultConfig.API_ENDPOINT,
                                       api_token=FlaskDefaultConfig.API_TOKEN,
                                       https=False, port=5000)
        self.adjuftments_plotting = AdjuftmentsPlotting()

    # noinspection PyProtectedMember
    def build_scheduler(self):
        # RUN THE STOCKS JOB EVERY 30 MINUTES DURING NYSE HOURS AND ALSO NIGHTLY @ 5:00AM
        stocks_trigger = OrTrigger([CronTrigger(day_of_week="MON,TUE,WED,THU,FRI",
                                                hour="9-16",
                                                minute="0/5",
                                                timezone=timezone("US/Eastern")),
                                    CronTrigger(hour="5",
                                                minute="0",
                                                timezone=self.local_timezone)])
        self.scheduler.add_job(func=self.adjuftments.refresh_stocks_data,
                               id="refresh_stocks_data",
                               name="Refresh Stocks Data",
                               trigger=stocks_trigger,
                               replace_existing=True)
        # CLEAN UP THE BUDGETS DATA NIGHTLY @ 5:01AM
        self.scheduler.add_job(func=self.adjuftments._clean_start_budgets_data,
                               id="sync_budgets_data",
                               name="Sync Budgets Data",
                               trigger=CronTrigger(hour="5",
                                                   minute="1"),
                               timezone=self.local_timezone,
                               replace_existing=True)
        # CLEAN UP THE MISCELLANEOUS DATA NIGHTLY @ 5:02AM
        self.scheduler.add_job(func=self.adjuftments._clean_start_miscellaneous_data,
                               id="sync_miscellaneous_data",
                               name="Sync Miscellaneous Data",
                               trigger=CronTrigger(hour="5",
                                                   minute="2"),
                               timezone=self.local_timezone,
                               replace_existing=True)
        # CLEAN UP THE MISCELLANEOUS DATA NIGHTLY @ 5:03AM
        self.scheduler.add_job(func=self.adjuftments._clean_start_stocks_data,
                               id="sync_stocks_data",
                               name="Sync Stocks Data",
                               trigger=CronTrigger(hour="5",
                                                   minute="3"),
                               timezone=self.local_timezone,
                               replace_existing=True)
        # CLEAN UP THE MISCELLANEOUS DATA NIGHTLY @ 5:04AM
        self.scheduler.add_job(func=self.adjuftments._clean_start_historic_expenses_data,
                               id="sync_historic_expenses_data",
                               name="Sync Historic Expenses Data",
                               trigger=CronTrigger(hour="5",
                                                   minute="4"),
                               timezone=self.local_timezone,
                               replace_existing=True)
        # REFRESH THE CATEGORIES NIGHTLY @ 5:05AM
        self.scheduler.add_job(func=self.adjuftments.refresh_categories_data,
                               id="refresh_categories_data",
                               name="Refresh Category Data",
                               trigger=CronTrigger(hour="5",
                                                   minute="5"),
                               timezone=self.local_timezone,
                               replace_existing=True)
        # REFRESH THE DASHBOARD NIGHTLY @ 5:06AM
        self.scheduler.add_job(func=self.adjuftments.refresh_dashboard,
                               id="refresh_dashboard_data",
                               name="Refresh Dashboard Data",
                               trigger=CronTrigger(hour="5",
                                                   minute="6"),
                               timezone=self.local_timezone,
                               replace_existing=True)
        # REFRESH THE IMAGES NIGHTLY @ 5:07AM
        self.scheduler.add_job(func=self.adjuftments_plotting.refresh_images,
                               id="refresh_images_data",
                               name="Refresh Images Data",
                               trigger=CronTrigger(hour="5",
                                                   minute="7"),
                               timezone=self.local_timezone,
                               replace_existing=True)
        # REFRESH THE STOCKS NIGHTLY @ 5:08AM
        self.scheduler.add_job(func=self.adjuftments_plotting.refresh_images,
                               id="refresh_images_data",
                               name="Refresh Images Data",
                               trigger=CronTrigger(hour="5",
                                                   minute="8"),
                               timezone=self.local_timezone,
                               replace_existing=True)

    def run_scheduled_events(self):
        """
        Run!

        Returns
        -------

        """
        self.build_scheduler()
        self.scheduler.start()

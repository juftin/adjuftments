#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Scheduling Tasks for Adjuftments
"""

import logging
from os import getenv

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.blocking import BlockingScheduler
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
        logger.info(FlaskDefaultConfig.SQLALCHEMY_DATABASE_URI)
        self.scheduler = BlockingScheduler(
            jobstores=dict(default=SQLAlchemyJobStore(
                url=FlaskDefaultConfig.SQLALCHEMY_DATABASE_URI,
                tableschema="adjuftments",
                tablename="job_scheduler")),
            executors=dict(default=ThreadPoolExecutor(max_workers=3)),
            job_defaults=dict(coalesce=False, max_instances=3),
            timezone=self.local_timezone)
        self.adjuftments = Adjuftments(endpoint=FlaskDefaultConfig.API_ENDPOINT,
                                       api_token=FlaskDefaultConfig.API_TOKEN,
                                       https=False, port=5000)
        self.adjuftments_plotting = AdjuftmentsPlotting()

    # noinspection PyProtectedMember
    def build_scheduler(self):
        # RUN THE STOCKS JOB EVERY 30 MINUTES DURING NYSE HOURS
        self.scheduler.add_job(func=self.adjuftments.refresh_stocks_data,
                               id="refresh_stocks_data",
                               name="Refresh Stocks Data",
                               trigger=CronTrigger(day_of_week="MON,TUE,WED,THU,FRI",
                                                   hour="9-16",
                                                   minute="0/1"),
                               timezone=timezone("US/Eastern"),
                               replace_existing=True)
        # CLEAN UP THE BUDGETS DATA NIGHTLY @ 5:00AM
        self.scheduler.add_job(func=self.adjuftments._clean_start_budgets_data,
                               id="sync_budgets_data",
                               name="Sync Budgets Data",
                               trigger=CronTrigger(hour="5",
                                                   minute="0"),
                               timezone=self.local_timezone,
                               replace_existing=True)
        # CLEAN UP THE MISCELLANEOUS DATA NIGHTLY @ 5:01AM
        self.scheduler.add_job(func=self.adjuftments._clean_start_miscellaneous_data,
                               id="sync_miscellaneous_data",
                               name="Sync Miscellaneous Data",
                               trigger=CronTrigger(hour="5",
                                                   minute="1"),
                               timezone=self.local_timezone,
                               replace_existing=True)
        # CLEAN UP THE MISCELLANEOUS DATA NIGHTLY @ 5:02AM
        self.scheduler.add_job(func=self.adjuftments._clean_start_stocks_data,
                               id="sync_stocks_data",
                               name="Sync Stocks Data",
                               trigger=CronTrigger(hour="5",
                                                   minute="2"),
                               timezone=self.local_timezone,
                               replace_existing=True)
        # REFRESH THE IMAGES NIGHTLY @ 5:03AM
        self.scheduler.add_job(func=self.adjuftments_plotting.refresh_images,
                               id="sync_plotting_data",
                               name="Sync Plotting Data",
                               trigger=CronTrigger(hour="5",
                                                   minute="3"),
                               timezone=self.local_timezone,
                               replace_existing=True)
        # REFRESH THE CATEGORIES NIGHTLY @ 5:04AM
        self.scheduler.add_job(func=self.adjuftments.refresh_categories_data,
                               id="sync_categories_data",
                               name="Sync Category Data",
                               trigger=CronTrigger(hour="5",
                                                   minute="4"),
                               timezone=self.local_timezone,
                               replace_existing=True)
        # REFRESH THE DASHBOARD NIGHTLY @ 5:05AM
        self.scheduler.add_job(func=self.adjuftments.refresh_dashboard,
                               id="sync_dashboard_data",
                               name="Sync Dashboard Data",
                               trigger=CronTrigger(hour="5",
                                                   minute="5"),
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

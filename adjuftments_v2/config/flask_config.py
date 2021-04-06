#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Flask configuration.
"""

import logging
from os import environ, getenv
from os.path import abspath
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine.url import URL

from .file_config import DOT_ENV_FILE_PATH

load_dotenv(DOT_ENV_FILE_PATH, override=True)
logger = logging.getLogger(__name__)


class FlaskDefaultConfig(object):
    """
    Default Flask Config
    """

    FLASK_ENV = "development"
    TESTING = True
    DEBUG = True

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DRIVERNAME = "postgresql+psycopg2"
    DATABASE_USERNAME = environ["DATABASE_USER"]
    DATABASE_PASSWORD = environ["DATABASE_PASSWORD"]

    if getenv("DOCKER_ENVIRONMENT") is None:
        DATABASE_HOST = "localhost"
        API_ENDPOINT = "localhost"
    else:
        DATABASE_HOST = environ["DATABASE_HOST"]
        API_ENDPOINT = environ["ADJUFTMENTS_API_HOST"]
    DATABASE_PORT = 5432
    DATABASE_NAME = environ["DATABASE_DB"]

    SQLALCHEMY_DATABASE_URI = URL(drivername=DRIVERNAME,
                                  username=DATABASE_USERNAME,
                                  password=DATABASE_PASSWORD,
                                  host=DATABASE_HOST,
                                  port=DATABASE_PORT,
                                  database=DATABASE_NAME)
    API_TOKEN = environ["ADJUFTMENTS_API_TOKEN"]
    SQLALCHEMY_ECHO = False


class FlaskTestingConfig(FlaskDefaultConfig):
    """
    Default Config + PostgreSQL Database Connection
    """
    config_dir = Path(abspath(__file__)).parent
    SQLALCHEMY_DATABASE_URI = "sqlite:////{config_dir}/sqlite.db"


class APIEndpoints(object):
    """
    API Endpoint Configuration
    """

    BASE_PATH: str = "api"
    API_VERSION: str = "1.0"
    URL_BASE: str = f"/{BASE_PATH}/{API_VERSION}"

    SPLITWISE_BASE: str = f"{URL_BASE}/splitwise"
    AIRTABLE_BASE: str = f"{URL_BASE}/airtable"
    ADJUFTMENTS_BASE: str = f"{URL_BASE}/adjuftments"
    FINANCE_BASE: str = f"{URL_BASE}/finance"
    ADMIN_BASE: str = f"{URL_BASE}/admin"

    AIRTABLE_BUDGETS: str = f"{AIRTABLE_BASE}/budgets"
    AIRTABLE_CATEGORIES: str = f"{AIRTABLE_BASE}/categories"
    AIRTABLE_DASHBOARD: str = f"{AIRTABLE_BASE}/dashboard"
    AIRTABLE_EXPENSE: str = f"{AIRTABLE_BASE}/expenses"
    AIRTABLE_MISCELLANEOUS: str = f"{AIRTABLE_BASE}/budgets"

    SPLITWISE_EXPENSES: str = f"{SPLITWISE_BASE}/expenses"
    SPLITWISE_BALANCE: str = f"{SPLITWISE_BASE}/balance"
    SPLITWISE_UPDATED_AT: str = f"{SPLITWISE_BASE}/timestamp"

    STOCK_TICKER_API: str = f"{FINANCE_BASE}/stocks"
    DASHBOARD_GENERATOR: str = f"{FINANCE_BASE}/dashboard"
    EXPENSE_CATEGORIES: str = f"{FINANCE_BASE}/categories"
    IMAGES_ENDPOINT: str = f"{FINANCE_BASE}/images"

    ADMIN_DATABASE_BUILD: str = f"{ADMIN_BASE}/build"
    ADMIN_USERS: str = f"{ADMIN_BASE}/users"
    HEALTHCHECK: str = f"{ADMIN_BASE}/health"

#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Flask configuration.
"""

from os import environ, path
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.engine.url import URL

config_dir = Path(path.abspath(__file__)).parent
env_file = path.join(config_dir.parent.parent, '.env')
load_dotenv(env_file, override=True)


class FlaskDefaultConfig(object):
    """
    Default Flask Config
    """

    FLASK_ENV = "development"
    TESTING = True
    DEBUG = True

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    _drivername = "postgresql"
    _username = environ["DATABASE_USER"]
    _password = environ["DATABASE_PASSWORD"]
    _host = environ["DATABASE_HOST"]
    _port = 5432
    _database = environ["DATABASE_DB"]

    SQLALCHEMY_DATABASE_URI = URL(drivername=_drivername,
                                  username=_username,
                                  password=_password,
                                  host=_host,
                                  port=_port,
                                  database=_database)
    SQLALCHEMY_ECHO = False


class FlaskTestingConfig(FlaskDefaultConfig):
    """
    Default Config + PostgreSQL Database Connection
    """
    SQLALCHEMY_DATABASE_URI = f"sqlite:////{config_dir}/sqlite.db"


class APIEndpoints(object):
    """
    API Endpoint Configuration
    """
    # api/1.0/splitwise/expenses
    BASE_PATH: str = "api"
    API_VERSION: str = "1.0"

    SPLITWISE_BASE: str = f"/{BASE_PATH}/{API_VERSION}/splitwise"
    AIRTABLE_BASE: str = f"/{BASE_PATH}/{API_VERSION}/airtable"
    ADJUFTMENTS_BASE: str = f"/{BASE_PATH}/{API_VERSION}/adjuftments"

    AIRTABLE_BUDGETS: str = f"{AIRTABLE_BASE}/budgets"
    AIRTABLE_CATEGORIES: str = f"{AIRTABLE_BASE}/categories"
    AIRTABLE_DASHBOARD: str = f"{AIRTABLE_BASE}/dashboard"
    AIRTABLE_EXPENSE: str = f"{AIRTABLE_BASE}/expenses"
    AIRTABLE_MISCELLANEOUS: str = f"{AIRTABLE_BASE}/budgets"
    SPLITWISE_EXPENSES: str = f"{SPLITWISE_BASE}/expenses"

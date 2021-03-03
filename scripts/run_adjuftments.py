#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Example Run All Script
"""
from json import loads
import logging

from requests import get, post

from adjuftments_v2.application import db

# filterwarnings("error")
logger = logging.getLogger(__name__)


def prepare_database(drop: bool = False):
    """
    Generate the Initial Database
    """
    from adjuftments_v2.models import ALL_TABLES
    logger.info(f"Preparing Database: {len(ALL_TABLES)} table(s)")
    if not db.engine.dialect.has_schema(db.engine, "adjuftments"):
        db.engine.execute("CREATE SCHEMA adjuftments;")
    if drop is True:
        db.drop_all()
    db.create_all()
    logger.info("Database Created")


def get_expenses_data():
    """
    Get and process some expenses data
    """
    airtable_response = get(url="http://webserver:5000/api/1.0/airtable/expenses",
                            params=dict(formula="OR({Imported}=True(), {Delete}=False())"))
    for response_content in loads(airtable_response.content):
        post(url="http://webserver:5000/api/1.0/adjuftments/expenses",
             json=response_content)


def get_splitwise_data():
    """
    Get and Process some Splitwise Data
    """
    airtable_response = get(url="http://webserver:5000/api/1.0/splitwise/expenses")
    for response_content in loads(airtable_response.content):
        post(url="http://webserver:5000/api/1.0/adjuftments/splitwise",
             json=response_content)


def get_budgets_data():
    """
    Get and process some budgets data
    """
    airtable_response = get(url="http://webserver:5000/api/1.0/airtable/budgets")
    for response_content in loads(airtable_response.content):
        post(url="http://webserver:5000/api/1.0/adjuftments/budgets",
             json=response_content)


def get_categories_data():
    """
    Get and process some categories data
    """
    airtable_response = get(url="http://webserver:5000/api/1.0/airtable/categories")
    for response_content in loads(airtable_response.content):
        post(url="http://webserver:5000/api/1.0/adjuftments/categories",
             json=response_content)


def get_dashboard_data():
    """
    Get and process some dashboard data
    """
    airtable_response = get(url="http://webserver:5000/api/1.0/airtable/dashboard")
    for response_content in loads(airtable_response.content):
        post(url="http://webserver:5000/api/1.0/adjuftments/dashboard",
             json=response_content)


def get_miscellaneous_data():
    """
    Get and process some miscellaneous data
    """
    airtable_response = get(url="http://webserver:5000/api/1.0/airtable/miscellaneous")
    for response_content in loads(airtable_response.content):
        post(url="http://webserver:5000/api/1.0/adjuftments/miscellaneous",
             json=response_content)


def clean_start(run: bool = True) -> None:
    """
    Refresh all Data!

    Parameters
    ----------
    run: bool

    Returns
    -------
    None
    """
    if run is True:
        get_budgets_data()
        get_categories_data()
        get_dashboard_data()
        get_miscellaneous_data()
        get_splitwise_data()
        get_expenses_data()


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s [%(levelname)8s]: %(message)s [%(name)s]",
                        handlers=[logging.StreamHandler()],
                        level=logging.INFO)
    prepare_database(drop=True)
    clean_start(run=True)

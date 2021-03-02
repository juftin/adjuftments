#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Example Run All Script
"""

import logging

from adjuftments_v2 import Airtable, db, Splitwise
from adjuftments_v2.config import AirtableConfig, SplitwiseConfig

# filterwarnings("error")
logger = logging.getLogger(__name__)


def prepare_database():
    """
    Generate the Initial Database
    """
    from adjuftments_v2.models import ALL_TABLES
    logger.info(f"Preparing Database: {len(ALL_TABLES)} table(s)")
    if not db.engine.dialect.has_schema(db.engine, "adjuftments"):
        db.engine.execute("CREATE SCHEMA adjuftments;")
    # db.drop_all()
    db.create_all()
    logger.info("Database Created")


def get_expenses_data():
    """
    Get and process some expenses data
    """
    airtableExpenses = Airtable(base=AirtableConfig.AIRTABLE_BASE,
                                table="expenses")
    airtable_records = airtableExpenses.get_all(formula="OR({Imported}=FALSE(), {Delete}=True())")
    for airtable_record in airtable_records:
        new_db_expense = airtableExpenses.get_expenses_row(airtable_record=airtable_record)
        airtable_response = db.session.merge(new_db_expense)
        # airtableExpenses.update(record_id=response.id, fields=dict(ImportedAt=str(response.ImportedAt),
        #                                                            Imported=response.Imported),
        #                         typecast=True)
        db.session.commit()
        logger.info(
            f"ExpensesTable: {airtable_response.id} - {airtable_response.amount}")


def get_splitwise_data():
    """
    Get and Process some Splitwise Data
    """
    splitwiseObj = Splitwise(consumer_key=SplitwiseConfig.SPLITWISE_CONSUMER_KEY,
                             consumer_secret=SplitwiseConfig.SPLITWISE_CONSUMER_SECRET,
                             access_token=SplitwiseConfig.SPLITWISE_ACCESS_TOKEN,
                             significant_other=SplitwiseConfig.SPLITWISE_SIGNIFICANT_OTHER)
    splitwise_records = splitwiseObj.get_expenses()
    for splitwise_record in splitwise_records:
        new_splitwise_expense = splitwiseObj.get_row(splitwise_record=splitwise_record)
        splitwise_response = db.session.merge(new_splitwise_expense)
        db.session.commit()
        logger.info(
            f"SplitwiseTable: {splitwise_response.id} - {splitwise_response.transaction_balance}")


def get_budgets_data():
    """
    Get and process some budgets data
    """
    airtableBudgets = Airtable(base=AirtableConfig.AIRTABLE_BASE,
                               table="budgets")
    airtable_records = airtableBudgets.get_all()
    for airtable_record in airtable_records:
        new_budget = airtableBudgets.get_budgets_row(airtable_record=airtable_record)
        budget_response = db.session.merge(new_budget)
        db.session.commit()
        logger.info(
            f"BudgetsTable: {budget_response.id} - {budget_response.month}")


def get_categories_data():
    """
    Get and process some categories data
    """
    airtableCategories = Airtable(base=AirtableConfig.AIRTABLE_BASE,
                                  table="categories")
    airtable_records = airtableCategories.get_all()
    for airtable_record in airtable_records:
        new_category = airtableCategories.get_categories_row(airtable_record=airtable_record)
        category_response = db.session.merge(new_category)
        db.session.commit()
        logger.info(
            f"CategoriesTable: {category_response.id} - {category_response.category}")


def get_dashboard_data():
    """
    Get and process some categories data
    """
    airtableDashboard = Airtable(base=AirtableConfig.AIRTABLE_BASE,
                                 table="dashboard")
    airtable_records = airtableDashboard.get_all()
    for airtable_record in airtable_records:
        new_dashboard = airtableDashboard.get_dashboard_row(airtable_record=airtable_record)
        dashboard_response = db.session.merge(new_dashboard)
        db.session.commit()
        logger.info(
            f"DashboardTable: {dashboard_response.id} - {dashboard_response.measure}")


def get_miscellaneous_data():
    """
    Get and process some categories data
    """
    airtableDashboard = Airtable(base=AirtableConfig.AIRTABLE_BASE,
                                 table="dashboard")
    airtable_records = airtableDashboard.get_all()
    for airtable_record in airtable_records:
        new_miscellaneous = airtableDashboard.get_miscellaneous_row(airtable_record=airtable_record)
        miscellaneous_response = db.session.merge(new_miscellaneous)
        db.session.commit()
        logger.info(
            f"MiscellaneousTable: {miscellaneous_response.id} - {miscellaneous_response.measure}")


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s [%(levelname)8s]: %(message)s [%(name)s]",
                        handlers=[logging.StreamHandler()],
                        level=logging.INFO)
    prepare_database()
    get_budgets_data()
    get_categories_data()
    get_dashboard_data()
    get_miscellaneous_data()
    get_splitwise_data()
    get_expenses_data()

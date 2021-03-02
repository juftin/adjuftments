#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Airtable interactions
"""

from datetime import datetime

from airtable import Airtable as AirtablePythonWrapper

from adjuftments_v2.config import AirtableConfig
from adjuftments_v2.models import BudgetsTable, CategoriesTable, DashboardTable, ExpensesTable, \
    MiscellaneousTable


class Airtable(AirtablePythonWrapper):
    """
    Python Class for interacting with Airtable
    """
    __VERSION__ = 2.0

    def __init__(self, base: str, table: str, api_key: str = None) -> None:
        """
        Instantiation of Airtable Class. Requires Base, Table, and API Key

        Parameters
        ----------
        base: str
            Airtable Base Identifier
        table: str
            Airtable Table Name
        api_key: str
            Airtable API Key. Defaults to `AIRTABLE_API_KEY` environement variable
            if not supplied
        """
        self.base = base
        self.table = table
        if api_key is None:
            self.api_key = AirtableConfig.AIRTABLE_API_KEY
        elif api_key is not None:
            self.api_key = api_key

        super().__init__(base_key=self.base,
                         table_name=self.table,
                         api_key=self.api_key)

    def __repr__(self) -> str:
        """
        String Representation
        """
        return f"<Airtable: {self.table}>"

    @staticmethod
    def get_expenses_row(airtable_record: dict) -> ExpensesTable:
        """
        Prepare a record for the Expenses Table

        Parameters
        ----------
        airtable_record: dict

        Returns
        -------
        ExpensesTable
        """
        new_expense = ExpensesTable(id=airtable_record["id"],
                                    amount=round(airtable_record["fields"].get("Amount"), 2),
                                    category=airtable_record["fields"].get("Category"),
                                    date=airtable_record["fields"].get("Date"),
                                    imported=True,
                                    imported_at=str(datetime.utcnow()),
                                    transaction=airtable_record["fields"].get("Transaction"),
                                    uuid=airtable_record["fields"].get("UUID"),
                                    splitwise_id=airtable_record["fields"].get("splitwiseID"),
                                    created_at=airtable_record["createdTime"])
        return new_expense

    @staticmethod
    def _process_expense_response(expense_record: dict) -> dict:
        """
        Prepare a record for the Budgets table

        Parameters
        ----------
        expense_record: dict

        Returns
        -------
        dict
        """
        processed_response = dict(
            id=expense_record["id"],
            amount=round(expense_record["fields"].get("Amount"), 2),
            category=expense_record["fields"].get("Category"),
            date=expense_record["fields"].get("Date"),
            imported=expense_record["fields"].get("Date"),
            imported_at=expense_record["fields"].get("Imported At"),
            transaction=expense_record["fields"].get("Transaction"),
            uuid=expense_record["fields"].get("UUID"),
            splitwise_id=expense_record["fields"].get("splitwiseID"),
            created_at=expense_record["createdTime"])
        return processed_response

    @staticmethod
    def get_budgets_row(airtable_record: dict) -> BudgetsTable:
        """
        Prepare a record for the Budgets table

        Parameters
        ----------
        airtable_record: dict

        Returns
        -------
        BudgetsTable
        """
        new_budget = BudgetsTable(
            id=airtable_record["id"],
            month=airtable_record["fields"]["Month"],
            proposed_budget=round(airtable_record["fields"]["Proposed Budget"], 2),
            actual_budget=round(airtable_record["fields"]["Actual Budget"], 2),
            proposed_savings=round(airtable_record["fields"]["Proposed Savings"], 2),
            amount_saved=round(airtable_record["fields"]["Amount Saved"], 2),
            amount_spent=round(airtable_record["fields"]["Amount Spent"], 2),
            amount_earned=round(airtable_record["fields"]["Amount Earned"], 2),
            created_at=airtable_record["createdTime"])
        return new_budget

    @staticmethod
    def get_categories_row(airtable_record: dict) -> CategoriesTable:
        """
        Prepare a record for the Categories table

        Parameters
        ----------
        airtable_record: dict

        Returns
        -------
        CategoriesTable
        """
        new_category = CategoriesTable(
            id=airtable_record["id"],
            category=airtable_record["fields"]["Category"],
            amount_spent=airtable_record["fields"]["Amount Spent"],
            percent_of_total=airtable_record["fields"]["% of Total"],
            created_at=airtable_record["createdTime"])
        return new_category

    @staticmethod
    def get_dashboard_row(airtable_record: dict) -> DashboardTable:
        """
        Prepare a record for the Dashboard Table

        Parameters
        ----------
        airtable_record: dict

        Returns
        -------
        DashboardTable
        """
        new_dashboard = DashboardTable(
            id=airtable_record["id"],
            measure=airtable_record["fields"]["Measure"],
            value=airtable_record["fields"]["Value"],
            created_at=airtable_record["createdTime"])
        return new_dashboard

    @staticmethod
    def get_miscellaneous_row(airtable_record: dict) -> MiscellaneousTable:
        """
        Prepare a record for the Miscellaneous Table

        Parameters
        ----------
        airtable_record: dict

        Returns
        -------
        DashboardTable
        """
        new_miscellaneous = MiscellaneousTable(
            id=airtable_record["id"],
            measure=airtable_record["fields"]["Measure"],
            value=airtable_record["fields"]["Value"],
            created_at=airtable_record["createdTime"])
        return new_miscellaneous

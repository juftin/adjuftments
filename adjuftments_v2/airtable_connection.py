#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Airtable interactions
"""

from datetime import datetime
from typing import List

from airtable import Airtable as AirtablePythonWrapper
from pandas import DataFrame

from adjuftments_v2.config import AirtableColumnMapping, AirtableConfig
from adjuftments_v2.models import (BudgetsTable, CategoriesTable,
                                   DashboardTable, ExpensesTable,
                                   MiscellaneousTable)


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
    def process_airtable_response(table: str, response: dict) -> dict:
        """
        Properly process an Airtable Response given a table name

        Parameters
        ----------
        table
        response

        Returns
        -------
        dict
        """
        if table.lower() == "expenses":
            updated_response = Airtable._process_expense_response(airtable_response=response)
        elif table.lower() in ["dashboard", "miscellaneous"]:
            updated_response = Airtable._process_measure_value_response(airtable_response=response)
        elif table.lower() == "budgets":
            updated_response = Airtable._process_budgets_response(airtable_response=response)
        elif table.lower() == "categories":
            updated_response = Airtable._process_categories_response(airtable_response=response)
        elif table.lower() == "stocks":
            updated_response = Airtable._process_stocks_response(airtable_response=response)
        else:
            updated_response = response
        return updated_response

    @staticmethod
    def get_column_mapping_json(table: str, airtable_dict: dict) -> dict:
        """
        Remap Normalized Column Names to Airtable

        Parameters
        ----------
        table : str
        airtable_dict: dict

        Returns
        -------
        dict
        """
        if table == "expenses":
            update_json = dict()
            for key, value in airtable_dict.items():
                updated_dict_key = AirtableColumnMapping.ExpensesReverse[key]
                # DO NOT UPDATE COMPUTED VALUES
                if key != "updated_at":
                    update_json[updated_dict_key] = value
        else:
            update_json = airtable_dict
        return update_json

    @staticmethod
    def get_expenses_row(expense_dict: dict) -> ExpensesTable:
        """
        Prepare a record for the Expenses Table

        Parameters
        ----------
        expense_dict: dict

        Returns
        -------
        ExpensesTable
        """
        new_expense = ExpensesTable(id=expense_dict["id"],
                                    amount=expense_dict["amount"],
                                    category=expense_dict["category"],
                                    date=expense_dict["date"],
                                    imported=expense_dict["imported"],
                                    imported_at=expense_dict["imported_at"],
                                    transaction=expense_dict["transaction"],
                                    uuid=expense_dict["uuid"],
                                    splitwise=expense_dict["splitwise"],
                                    splitwise_id=expense_dict["splitwise_id"],
                                    created_at=expense_dict["created_at"],
                                    delete=expense_dict["delete"])
        return new_expense

    @staticmethod
    def get_budgets_row(budgets_dict: dict) -> BudgetsTable:
        """
        Prepare a record for the Budgets table

        Parameters
        ----------
        budgets_dict: dict

        Returns
        -------
        BudgetsTable
        """
        new_budget = BudgetsTable(
            id=budgets_dict["id"],
            month=budgets_dict["month"],
            proposed_budget=budgets_dict["proposed_budget"],
            actual_budget=budgets_dict["actual_budget"],
            proposed_savings=budgets_dict["proposed_savings"],
            amount_saved=budgets_dict["amount_saved"],
            amount_spent=budgets_dict["amount_spent"],
            amount_earned=budgets_dict["amount_earned"],
            created_at=budgets_dict["created_at"])
        return new_budget

    @staticmethod
    def get_categories_row(categories_dict: dict) -> CategoriesTable:
        """
        Prepare a record for the Categories table

        Parameters
        ----------
        categories_dict: dict

        Returns
        -------
        CategoriesTable
        """
        new_category = CategoriesTable(
            id=categories_dict["id"],
            category=categories_dict["category"],
            amount_spent=categories_dict["amount_spent"],
            percent_of_total=categories_dict["percent_of_total"],
            created_at=categories_dict["created_at"])
        return new_category

    @staticmethod
    def get_dashboard_row(dashboard_dict: dict) -> DashboardTable:
        """
        Prepare a record for the Dashboard Table

        Parameters
        ----------
        dashboard_dict: dict

        Returns
        -------
        DashboardTable
        """
        new_dashboard = DashboardTable(
            id=dashboard_dict["id"],
            measure=dashboard_dict["measure"],
            value=dashboard_dict["value"],
            created_at=dashboard_dict["created_at"])
        return new_dashboard

    @staticmethod
    def get_miscellaneous_row(miscellaneous_dict: dict) -> MiscellaneousTable:
        """
        Prepare a record for the Miscellaneous Table

        Parameters
        ----------
        miscellaneous_dict: dict

        Returns
        -------
        DashboardTable
        """
        new_miscellaneous = MiscellaneousTable(
            id=miscellaneous_dict["id"],
            measure=miscellaneous_dict["measure"],
            value=miscellaneous_dict["value"],
            created_at=miscellaneous_dict["created_at"])
        return new_miscellaneous

    @staticmethod
    def expenses_as_df(expense_array: object) -> object:
        """
        Return Expenses as Pandas Dataframe

        Parameters
        ----------
        expense_array: List[dict]

        Returns
        -------
        DataFrame
        """
        expense_df = DataFrame(expense_array,
                               columns=AirtableColumnMapping.EXPENSES_COLUMN_ORDERING)
        return expense_df.astype(AirtableColumnMapping.EXPENSES_DTYPE_MAPPING)

    @staticmethod
    def _process_expense_response(airtable_response: dict) -> dict:
        """
        Prepare a flattened dict with all columns (using defaults if needed)
        from an Airtable response for Expenses

        Parameters
        ----------
        airtable_response: dict

        Returns
        -------
        dict
        """
        expense_date = airtable_response["fields"].get("Date", None)
        if expense_date is not None:
            expense_date = datetime.strptime(expense_date, "%Y-%m-%d")

        return dict(
            id=airtable_response["id"],
            amount=round(airtable_response["fields"].get("Amount", 0.00), 2),
            category=airtable_response["fields"].get("Category", None),
            date=expense_date,
            imported=airtable_response["fields"].get("Imported", False),
            imported_at=airtable_response["fields"].get("ImportedAt", None),
            transaction=airtable_response["fields"].get("Transaction", None),
            uuid=airtable_response["fields"].get("UUID", None),
            splitwise=airtable_response["fields"].get("Splitwise", False),
            splitwise_id=airtable_response["fields"].get("splitwiseID", None),
            created_at=airtable_response["createdTime"],
            delete=airtable_response["fields"].get("Delete", False),
            updated_at=airtable_response["fields"].get("ModifiedAt", None))

    @staticmethod
    def _process_categories_response(airtable_response: dict) -> dict:
        """
        Prepare a record for the Categories table

        Parameters
        ----------
        airtable_response: dict

        Returns
        -------
        CategoriesTable
        """
        new_category = dict(
            id=airtable_response["id"],
            category=airtable_response["fields"]["Category"],
            amount_spent=airtable_response["fields"]["Amount Spent"],
            percent_of_total=airtable_response["fields"]["% of Total"],
            created_at=airtable_response["createdTime"])
        return new_category

    @staticmethod
    def _process_stocks_response(airtable_response: dict) -> dict:
        """
        Prepare a record for the Stocks table

        Parameters
        ----------
        airtable_response: dict

        Returns
        -------
        CategoriesTable
        """
        stock_response = dict(
            id=airtable_response["id"],
            ticker=airtable_response["fields"].get("Ticker", None),
            stock_price=airtable_response["fields"].get("Stock Price", None),
            value=airtable_response["fields"].get("Value", None),
            holdings=airtable_response["fields"].get("Holdings", None),
            description=airtable_response["fields"].get("Description", None),
            cost_basis=airtable_response["fields"].get("Cost Basis", None),
            created_at=airtable_response["createdTime"])
        return stock_response

    @staticmethod
    def _process_budgets_response(airtable_response: dict) -> BudgetsTable:
        """
        Prepare a record for the Budgets table

        Parameters
        ----------
        airtable_response: dict

        Returns
        -------
        BudgetsTable
        """
        new_budget = dict(
            id=airtable_response["id"],
            month=airtable_response["fields"]["Month"],
            proposed_budget=round(airtable_response["fields"]["Proposed Budget"], 2),
            actual_budget=round(airtable_response["fields"]["Actual Budget"], 2),
            proposed_savings=round(airtable_response["fields"]["Proposed Savings"], 2),
            amount_saved=round(airtable_response["fields"]["Amount Saved"], 2),
            amount_spent=round(airtable_response["fields"]["Amount Spent"], 2),
            amount_earned=round(airtable_response["fields"]["Amount Earned"], 2),
            created_at=airtable_response["createdTime"])
        return new_budget

    @staticmethod
    def _process_measure_value_response(airtable_response: dict) -> dict:
        """
        Prepare a flattened dict with all columns (using defaults if needed)
        from a generic Measure, Value table

        Parameters
        ----------
        airtable_response: dict

        Returns
        -------
        dict
        """
        return dict(
            id=airtable_response["id"],
            measure=airtable_response["fields"].get("Measure"),
            value=airtable_response["fields"].get("Value"),
            created_at=airtable_response["createdTime"])

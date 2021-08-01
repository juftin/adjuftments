#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Dashboard Formatting
"""

from calendar import monthrange
from datetime import datetime
import logging
from typing import Dict, List, Optional, Tuple

from dateutil.relativedelta import relativedelta
from numpy import where
from pandas import DataFrame, Series

from adjuftments import Airtable
from adjuftments.application import db_session
from adjuftments.config import AirtableConfig, DashboardConfig
from adjuftments.schema import (AccountsTable, BudgetsTable,
                                DashboardTable, ExpensesTable,
                                MiscellaneousTable)
from adjuftments.utils import AdjuftmentsEncoder

logger = logging.getLogger(__name__)


class Dashboard(object):
    """
    Adjuftments Dashboarding Functions, everything is a class or staticmethod
    """

    @classmethod
    def _percent_through_month(cls) -> float:
        """
        Return percent through Current Month as a float
        """
        current_timestamp = datetime.now()
        beginning_of_month, end_of_month = monthrange(year=current_timestamp.year,
                                                      month=current_timestamp.month)
        total_seconds_in_month = end_of_month * (24 * 60 * 60)
        passed_seconds_in_month = (current_timestamp.day - 1) * (24 * 60 * 60)
        beginning_of_day = current_timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_passed_today = (current_timestamp - beginning_of_day).total_seconds()
        total_seconds_passed = seconds_passed_today + passed_seconds_in_month
        percentage_though_month = total_seconds_passed / total_seconds_in_month
        return percentage_though_month

    @classmethod
    def _get_current_budget(cls) -> float:
        """
        Get the current month's budget from the database

        Returns
        -------
        float
            Current Budget
        """
        query_filter = dict(month=datetime.now().strftime(format="%B"))
        response = BudgetsTable.query.filter_by(**query_filter).first()
        formatted_response = AdjuftmentsEncoder.parse_object(obj=response.to_dict())
        current_budget = formatted_response["proposed_budget"]
        return current_budget

    @classmethod
    def _filter_to_current_month(cls, dataframe: DataFrame, date_column: str) -> DataFrame:
        """
        Filter a Dataframe to a current month

        Parameters
        ----------
        dataframe
        date_column

        Returns
        -------
        DataFrame
        """
        current_time = datetime.now()
        month_from_now = current_time + relativedelta(months=1)
        next_month = month_from_now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_dataframe = dataframe.loc[(dataframe[date_column] >= this_month) &
                                      (dataframe[date_column] < next_month)].copy()
        return new_dataframe.reset_index(drop=True)

    @classmethod
    def _summarize_monthly_rollup(cls, dataframe: DataFrame) -> dict:
        """
        Summarize by Category - But handle exceptions for Savings Spend

        Parameters
        ----------
        dataframe: DataFrame

        Returns
        -------
        dict
        """
        current_months_data = cls._filter_to_current_month(dataframe=dataframe,
                                                           date_column="date")
        current_months_data["updated_amount"] = where(
            current_months_data["category"] == "Savings Spend",
            -current_months_data["amount"],
            current_months_data["amount"])
        monthly_totals = current_months_data.groupby(["expense_type"])[
            "updated_amount"].sum().to_dict()
        del current_months_data
        return monthly_totals

    @classmethod
    def _get_monthly_totals(cls, dataframe: DataFrame) -> dict:
        """
        Get Monthly Summary from Expense Dataframe

        Parameters
        ----------
        dataframe

        Returns
        -------
        dict
        """
        prepared_dict = dict()
        # THIS IS THE ONE VARIABLE THAT DOESN'T COME FROM THIS MONTH
        reimbursement_total = dataframe[dataframe["expense_type"] ==
                                        "Reimbursement"]["amount"].sum()
        prepared_dict["total_reimbursement"] = reimbursement_total
        # UPDATE SOME OTHER MONTHLY VALUES
        prepared_dict["percent_through_month"] = cls._percent_through_month()
        prepared_dict["current_budget"] = cls._get_current_budget()
        # FILTER THE DATA TO CURRENT DATE
        updated_categories = cls._summarize_monthly_rollup(dataframe=dataframe)
        prepared_dict["monthly_housing"] = updated_categories.get("Housing", 0.0)
        prepared_dict["monthly_savings"] = updated_categories.get("Savings", 0.0)
        prepared_dict["monthly_income"] = updated_categories.get("Income", 0.0)
        prepared_dict["monthly_adjustments"] = updated_categories.get("Adjustment", 0.0)
        prepared_dict["monthly_expenses"] = updated_categories.get("Expense", 0.0)
        # PERFORM SOME AGGREGATIONS
        amount_under_budget = \
            (prepared_dict["percent_through_month"] * prepared_dict["current_budget"]) - \
            prepared_dict["monthly_expenses"]
        prepared_dict["amount_under_budget"] = amount_under_budget
        prepared_dict["amount_budget_left"] = \
            prepared_dict["current_budget"] - prepared_dict["monthly_expenses"]
        prepared_dict["percent_budget_spent"] = \
            prepared_dict["monthly_expenses"] / prepared_dict["current_budget"]
        prepared_dict["percent_budget_left"] = 1 - prepared_dict["percent_budget_spent"]
        return prepared_dict

    @classmethod
    def _get_value_from_dataframe(cls, dataframe: DataFrame, measure: str, value: str,
                                  returned_column: str) -> object:
        """
        Parse a DataFrame and return a single value

        Parameters
        ----------
        dataframe: DataFrame
        measure: str
            Column Name
        value: str
            Column Value

        Returns
        -------
        object
        """
        returned_value = dataframe[dataframe[measure] == value][returned_column].values
        if len(returned_value) > 1:
            logger.warning(f"Dataframe query returned more than one result: {measure} {value}")
        return returned_value[0]

    @classmethod
    def _expected_income(cls, pay_check_count: int, bimonthly_income: float) -> float:
        """
        Calculate Remaining Expected Monthly Income (Assumes 24 pay periods)

        Parameters
        ----------
        pay_check_count: int
            Amount of paychecks received in a month
        bimonthly_income: float
            How much earned every two weeks

        Returns
        -------
        float
        """
        if pay_check_count == 0:
            expected_income = 2 * bimonthly_income
        elif pay_check_count == 1:
            expected_income = 1 * bimonthly_income
        elif pay_check_count >= 2:
            expected_income = 0 * bimonthly_income
        return expected_income

    @classmethod
    def _get_miscellaneous_data(cls) -> dict:
        """
        Get the Miscellaneous Table as a Dict

        Returns
        -------
        dict
        """
        database_response = MiscellaneousTable.query.all()
        compiled_response = list()
        for record in database_response:
            cleaned_response = AdjuftmentsEncoder.parse_object(obj=record.to_dict())
            compiled_response.append(cleaned_response)
        miscellaneous_df = DataFrame(compiled_response)
        miscellaneous_dict = \
            miscellaneous_df[["measure", "value"]]. \
                set_index("measure"). \
                to_dict(orient="dict")["value"]
        return miscellaneous_dict

    @classmethod
    def _get_paycheck_count(cls, dataframe: DataFrame, employer: List[str]) -> float:
        """
        Get Current Month's Paycheck Count from Dataframe

        Parameters
        ----------
        dataframe: DataFrame
        employer: List[str]

        Returns
        -------
        float
        """
        current_month_df = cls._filter_to_current_month(dataframe=dataframe,
                                                        date_column="date")
        current_month_income = current_month_df.loc[
            current_month_df["expense_type"] == "Income"].copy()
        del current_month_df
        current_month_income["possible_employer"] = current_month_income["transaction"].apply(
            lambda x: x.split(" - ")[0].upper())
        current_month_income["possible_salary_string"] = current_month_income["transaction"].apply(
            lambda x: x.split(" - ")[1].upper())
        paycheck_count = len(
            current_month_income.loc[
                (current_month_income["possible_employer"].isin(employer)) &
                (current_month_income["possible_salary_string"] == "SALARY")
                ]
        )
        del current_month_income
        return paycheck_count

    @classmethod
    def _get_amount_to_save(cls, dataframe: DataFrame, finance_dict: dict) -> dict:
        """
        Get the projected amount to save at given point in the month

        Parameters
        ----------
        dataframe: DataFrame
            EXPENSES Dataframe

        Returns
        -------
        dict
        """
        miscellaneous_dict = cls._get_miscellaneous_data()
        employer_str = miscellaneous_dict["Employer"].split(",")
        employers = [employer.upper() for employer in employer_str]
        paycheck_count = cls._get_paycheck_count(dataframe=dataframe, employer=employers)
        housing_amount = float(miscellaneous_dict["Monthly Rent"])
        bimonthly_income = float(miscellaneous_dict["Bi-Monthly Salary"])
        monthly_starting_balance = float(miscellaneous_dict["Monthly Starting Balance"])

        current_time = datetime.now()
        month_from_now = current_time + relativedelta(months=1)
        next_month = month_from_now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        next_month_rent = dataframe.loc[
            (dataframe["date"] >= next_month) &
            (dataframe["expense_type"] == "Housing")]["amount"].sum()

        money_left_to_spend = finance_dict["checking_balance"] - \
                              finance_dict["amount_budget_left"]
        money_left_after_rent = money_left_to_spend - (housing_amount - next_month_rent)
        expected_income = cls._expected_income(pay_check_count=paycheck_count,
                                               bimonthly_income=bimonthly_income)
        money_left_after_income = money_left_after_rent + expected_income
        money_left_after_prorated_adj = money_left_after_income + \
                                        finance_dict["amount_under_budget"] - \
                                        monthly_starting_balance
        money_left_after_reimbursement = money_left_after_prorated_adj + \
                                         finance_dict["total_reimbursement"]
        amount_to_save = money_left_after_reimbursement
        return amount_to_save

    @classmethod
    def _get_dashboard_dict(cls, dataframe: DataFrame,
                            updated_data: bool = False) -> dict:
        """
        Run the full thing

        Parameters
        ----------
        dataframe: DataFrame
            Pandas dataframe to generate dashboard from
        updated_data: bool
            Whether there is new data or not. If new data is available, triggers account
            balance update

        Returns
        -------
        dict
        """
        bank_account_data = AccountsTable.query.all()
        formatted_account_data = AdjuftmentsEncoder.parse_table_response_array(bank_account_data)
        balanced_data, account_balances = cls._balance_df(
            expense_df=dataframe,
            bank_account_records=formatted_account_data)
        if updated_data is True:
            cls._handle_account_balance_update(account_data=account_balances)
        monthly_totals = cls._get_monthly_totals(dataframe=balanced_data)
        balance_dict = cls._process_account_balances(account_balances=account_balances)
        finance_dict = dict(**monthly_totals, **balance_dict)
        finance_dict["amount_to_save"] = cls._get_amount_to_save(dataframe=balanced_data,
                                                                 finance_dict=finance_dict)
        budget_dict = cls._get_budget_based_calculations(finance_dict=finance_dict)
        update_dict = cls._get_final_dashboard_updates()
        prepared_dashboard_dict = dict(**finance_dict, **budget_dict, **update_dict)
        return prepared_dashboard_dict

    @classmethod
    def _handle_account_balance_update(cls, account_data: dict) -> List[dict]:
        """
        Run the full thing

        Parameters
        ----------
        account_data: dict
            Dictionary of bank account data

        Returns
        -------
        dict
        """
        balance_manifest = list()
        for account_name, account_record in account_data["Checking"].items():
            matching_record = AccountsTable.query.get(account_record["record_id"])
            matching_record.balance = account_record["balance"]
            db_session.merge(matching_record)
            db_session.commit()
            balance_manifest.append(dict(id=account_record["record_id"],
                                         balance=account_record["balance"]))
        for savings_account_name, savings_account_record in account_data["Savings"].items():
            matching_record = AccountsTable.query.get(savings_account_record["record_id"])
            matching_record.balance = savings_account_record["balance"]
            db_session.merge(matching_record)
            db_session.commit()
            balance_manifest.append(dict(id=savings_account_record["record_id"],
                                         balance=savings_account_record["balance"]))
        return balance_manifest

    @staticmethod
    def run_dashboard(dataframe: DataFrame,
                      splitwise_balance: Optional[float] = None,
                      updated_data: bool = False) -> List[dict]:
        """
        Run the whole gosh darn thing

        Parameters
        ----------
        dataframe : DataFrame
        splitwise_balance : bool
            Optional Updated Splitwise Balance
        updated_data: bool
            Whether there is new data or not. If new data is available, triggers account
            balance update

        Returns
        -------
        List[dict]
            Update Manifest
        """
        prepared_dashboard_dict = Dashboard._get_dashboard_dict(dataframe=dataframe,
                                                                updated_data=updated_data)
        if splitwise_balance is not None:
            prepared_dashboard_dict["splitwise_balance"] = splitwise_balance
        processed_dashboard_dict = Dashboard._process_dashboard_dict(
            dashboard_dict=prepared_dashboard_dict)
        db_update_manifest = Dashboard._unload_dashboard_dict_to_manifest(
            dashboard_dict=processed_dashboard_dict)
        final_manifest = Dashboard._unload_manifest_to_database(manifest=db_update_manifest)
        return final_manifest

    @classmethod
    def _get_budget_based_calculations(cls, finance_dict: dict) -> dict:
        """
        Generate some final Savings Based Calculations

        Parameters
        ----------
        finance_dict: dict
            Existing Dashboard Dict

        Returns
        -------
        dict
        """
        current_timestamp = datetime.now()
        beginning_of_month, end_of_month = monthrange(year=current_timestamp.year,
                                                      month=current_timestamp.month)
        planned_budget = finance_dict["current_budget"] / end_of_month
        adjusted_budget = finance_dict["amount_budget_left"] / (
                end_of_month - current_timestamp.day + 1)
        resulting_savings = finance_dict["amount_to_save"] + finance_dict[
            "total_savings"]
        potential_savings = resulting_savings + (
                finance_dict["amount_budget_left"] - finance_dict["amount_under_budget"])
        return dict(planned_budget=planned_budget,
                    adjusted_budget=adjusted_budget,
                    resulting_savings=resulting_savings,
                    potential_savings=potential_savings)

    @classmethod
    def _get_final_dashboard_updates(cls) -> dict:
        """
        Retrieve the Date Updated, and final expenses

        Returns
        -------
        dict
        """
        response = ExpensesTable.query.order_by(ExpensesTable.date.desc(),
                                                ExpensesTable.imported_at.desc()).first()
        final_expense_row = AdjuftmentsEncoder.parse_object(obj=response.to_dict())
        final_expense_date = datetime.fromisoformat(final_expense_row["date"]).strftime("%m/%d/%Y")
        final_expense_merchant = final_expense_row["transaction"].split(" - ")[0]
        final_expense_amount = AdjuftmentsEncoder.format_float(amount=final_expense_row["amount"],
                                                               float_format="money")
        final_expense_record = (f"{final_expense_date} - {final_expense_merchant} - "
                                f"{final_expense_amount}")
        date_updated = datetime.now().strftime("%I:%M %p, %m/%d/%Y")
        return dict(final_expense_record=final_expense_record,
                    date_updated=date_updated)

    @classmethod
    def _process_dashboard_dict(cls, dashboard_dict: dict) -> DataFrame:
        """
        Process the Dashboard Dictionary

        Parameters
        ----------
        dashboard_dict: dict
            Existing Dashboard Dict

        Returns
        -------
        DataFrame
        """
        updated_dict = dict()
        for key, value in dashboard_dict.items():
            try:
                updated_dict[DashboardConfig.DICT_TO_DASHBOARD[key]] = \
                    AdjuftmentsEncoder.format_float(
                        amount=value,
                        float_format=DashboardConfig.DICT_TO_FORMAT[key])
            except KeyError:
                pass
        return updated_dict

    @classmethod
    def _prepare_dashboard_dataframe(cls, dashboard_dict: dict) -> DataFrame:
        """
        Prepare the final Dashboard DataFrame

        Parameters
        ----------
        dashboard_dict: dict
            Existing Dashboard Dict

        Returns
        -------
        DataFrame
        """
        dashboard_df = Series(
            data=dashboard_dict,
            dtype=object,
            name="Value",
            index=DashboardConfig.DICT_TO_DASHBOARD.keys()).reset_index(drop=False)
        dashboard_df.rename(columns={"index": "Measure"}, inplace=True)
        for index, row in dashboard_df.iterrows():
            formatted_measure = DashboardConfig.DICT_TO_DASHBOARD[row["Measure"]]
            formatted_value = AdjuftmentsEncoder.format_float(
                amount=row["Value"],
                float_format=DashboardConfig.DICT_TO_FORMAT[row["Measure"]])
            dashboard_df.at[index, "Measure"] = formatted_measure
            dashboard_df.at[index, "Value"] = formatted_value
        return dashboard_df

    @classmethod
    def _unload_dashboard_dict_to_manifest(cls, dashboard_dict: dict) -> List[dict]:
        """
        Upload a Dashboard to a Manifest

        Parameters
        ----------
        dashboard_dict: dict
            Dashboard dictionary

        Returns
        -------
        List[dict]
        """
        manifest = list()
        for measure, value in dashboard_dict.items():
            try:
                dashboard_query = dict(measure=measure)
                existing_row: DashboardTable = DashboardTable.query.filter_by(
                    **dashboard_query).first()
                if existing_row is None:
                    manifest.append(dict(id=None, measure=measure, value=value))
                elif existing_row.value != value:
                    manifest.append(dict(id=existing_row.id, measure=existing_row.measure,
                                         value=value))
            except KeyError:
                pass
        return manifest

    @classmethod
    def _unload_manifest_to_database(cls, manifest: List[dict]) -> List[dict]:
        """
        Unload a prepared manifest into the Database

        Parameters
        ----------
        manifest: List[dict]
            Update manifest

        Returns
        -------
        List[dict]
        """
        airtable_dashboard = Airtable(base=AirtableConfig.AIRTABLE_BASE,
                                      table="dashboard")
        final_manifest = list()
        for update_manifest in manifest:
            if update_manifest["id"] is None:
                airtable_record = airtable_dashboard.insert(
                    fields=dict(Measure=update_manifest["measure"],
                                Value=update_manifest["value"]))
                record_to_update = DashboardTable(id=airtable_record["id"],
                                                  measure=update_manifest["measure"],
                                                  value=update_manifest["value"],
                                                  created_at=airtable_record["createdTime"])

            else:
                record_to_update: DashboardTable = DashboardTable.query.get(update_manifest["id"])
                if record_to_update is None:
                    record_to_update = DashboardTable(id=update_manifest["id"],
                                                      measure=update_manifest["measure"],
                                                      value=update_manifest["value"])
                else:
                    record_to_update.value = update_manifest["value"]
            db_session.merge(record_to_update)
            logger.info(
                f"Updating Dashboard: {record_to_update.measure} - {record_to_update.value}")
            db_session.commit()
            final_manifest.append(AdjuftmentsEncoder.parse_table_response(record_to_update))
        return final_manifest

    @classmethod
    def _process_bank_account_data(cls, bank_account_array: List[dict]) -> Tuple[str, dict]:
        """
        Process Bank Account Data and return the checking account and mapping dictionary

        Parameters
        ----------
        bank_account_array: List[dict]
            Bank account data array

        Returns
        -------
        Tuple[str, dict]
            (checking_account_name, bank_account_mapping)
        """
        bank_account_df = DataFrame(data=bank_account_array)
        checking_account_name = \
            bank_account_df[bank_account_df["type"] == "Checking"].reset_index().at[0, "name"]
        bank_account_mapping = bank_account_df.set_index("name").to_dict(orient="index")
        return checking_account_name, bank_account_mapping

    @classmethod
    def _get_account_impact_mapping(cls, checking_account: str, account_dict: Dict,
                                    transaction_data: dict) -> Dict[str, float]:
        """
        Get A Mapping of Which Account A Transaction Should Impact

        Parameters
        ----------
        checking_account: str
            Name of Primary Checking Account
        account_dict: dict
            Dictionary of Bank Account Data
        transaction_data: dict
            Data of underlying transaction

        Returns
        -------
        Returns a Bank Account Impact Dictionary
        """
        transaction_account_name = transaction_data["account_name"]
        transaction_amount = transaction_data["amount"]
        all_bank_account_names = set(account_dict.keys())
        balance_impact_column = f"{transaction_account_name}_impact".lower()
        checking_impact_column = f"{checking_account}_impact".lower()
        bank_account_impact = dict()

        if transaction_data["expense_type"] == "Savings" and \
                transaction_data["category"] != "Savings Spend":
            bank_account_impact[checking_impact_column] = -transaction_amount
            bank_account_impact[balance_impact_column] = transaction_amount
            non_impacted_accounts = all_bank_account_names - {checking_account,
                                                              transaction_account_name}
            for other_account_name in non_impacted_accounts:
                other_impact_column = f"{other_account_name}_impact".lower()
                bank_account_impact[other_impact_column] = 0
        elif transaction_data["expense_type"] == "Income":
            bank_account_impact[balance_impact_column] = transaction_amount
            for other_account_name in (all_bank_account_names - {transaction_account_name}):
                other_impact_column = f"{other_account_name}_impact".lower()
                bank_account_impact[other_impact_column] = 0
        else:
            bank_account_impact[balance_impact_column] = -transaction_amount
            for other_account_name in (all_bank_account_names - {transaction_account_name}):
                other_impact_column = f"{other_account_name}_impact".lower()
                bank_account_impact[other_impact_column] = 0
        return bank_account_impact

    @classmethod
    def _get_impacted_data(cls, expense_df: DataFrame, checking_account: str,
                           account_dict: dict) -> DataFrame:
        """
        Get the Impact Of Every Expense On All Accounts with New Impact Columns

        Parameters
        ----------
        expense_df: DataFrame
            DataFrame of expense data
        checking_account: str
            Name of Checking Account
        account_dict: dict
            Dict of Account data

        Returns
        -------
        DataFrame
        """
        updated_dataframe = expense_df.copy()
        updated_dataframe.sort_values(by=["date", "imported_at", "created_at"],
                                      ascending=True, inplace=True)
        updated_dataframe.reset_index(drop=True, inplace=True)
        updated_dataframe["expense_type"] = updated_dataframe.apply(
            lambda x: AdjuftmentsEncoder.categorize_expenses(category=x.category,
                                                             transaction=x.transaction),
            axis=1)
        account_impact_data = updated_dataframe.apply(
            lambda x: cls._get_account_impact_mapping(checking_account=checking_account,
                                                      account_dict=account_dict,
                                                      transaction_data=x), axis=1).apply(Series)
        joined_data = updated_dataframe.merge(right=account_impact_data, left_index=True,
                                              right_index=True)
        joined_data.sort_values(by=["date", "imported_at", "created_at"],
                                ascending=True, inplace=True)
        joined_data.reset_index(drop=True, inplace=True)
        return joined_data

    @classmethod
    def _get_account_balance_data(cls, expense_df: DataFrame, account_dict: dict):
        """
        Get the account balances from account Dictionary and expense data

        Parameters
        ----------
        expense_df: DataFrame
            DataFrame of expense data
        account_dict: dict
            Dict of Account data

        Returns
        -------
        """
        balanced_df = expense_df.copy()
        account_balance_dict = dict(Checking=dict(), Savings=dict())
        for bank_account_name, account_data in account_dict.items():
            impact_column = f"{bank_account_name}_impact".lower()
            balance_column = f"{bank_account_name}_balance".lower()
            balanced_df.at[0, impact_column] += account_data["starting_balance"]
            balanced_df[balance_column] = balanced_df[impact_column].cumsum()
            # PUT THE NEW DICT IN THE "CHECKING" / OR "SAVINGS" KEY
            account_balance_dict[account_data["type"]][bank_account_name] = dict(
                balance=balanced_df[balance_column].iloc[-1],
                column_name=balance_column,
                default=account_data["default"],
                record_id=account_data["id"])
        return balanced_df, account_balance_dict

    @classmethod
    def _balance_df(cls, expense_df: DataFrame, bank_account_records=List[dict]) -> DataFrame:
        """
        Update the EXPENSES Dataframe with the Balances of each transaction on
        account balances.

        Parameters
        ----------
        expense_df: DataFrame
                DataFrame of expense data
        bank_account_records: List[dict]
            Array of bank account records

        Returns
        -------
        DataFrame
        """
        checking_account, bank_account_dict = cls._process_bank_account_data(
            bank_account_array=bank_account_records)
        financial_impact_df = cls._get_impacted_data(expense_df=expense_df,
                                                     checking_account=checking_account,
                                                     account_dict=bank_account_dict)
        balanced_df, account_balances = cls._get_account_balance_data(
            expense_df=financial_impact_df,
            account_dict=bank_account_dict)
        return balanced_df, account_balances

    @classmethod
    def _process_account_balances(cls, account_balances: Dict[dict, dict]) -> dict:
        """
        Process Account Balances and Roll Up Total Amounts

        Parameters
        ----------
        account_balances: Dict[dict, dict]
            Account balances data

        Returns
        -------
        dict
        """
        checking_balance = 0
        savings_balance = 0
        net_worth = 0
        processed_balances = dict()
        for checking_account, checking_account_data in account_balances["Checking"].items():
            formatted_checking_name = f"{checking_account}_balance".lower()
            checking_balance += checking_account_data["balance"]
            net_worth += checking_account_data["balance"]
            processed_balances[formatted_checking_name] = checking_account_data["balance"]
        for savings_account, savings_account_data in account_balances["Savings"].items():
            formatted_savings_name = f"{savings_account}_balance".lower()
            savings_balance += savings_account_data["balance"]
            net_worth += savings_account_data["balance"]
            processed_balances[formatted_savings_name] = savings_account_data["balance"]

        processed_balances["checking_balance"] = checking_balance
        processed_balances["total_savings"] = savings_balance
        processed_balances["net_worth"] = net_worth
        return processed_balances

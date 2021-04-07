#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Dashboard Formatting
"""

from calendar import monthrange
from datetime import datetime
import logging
from typing import Dict, List, Optional

from dateutil.relativedelta import relativedelta
from numpy import where
from pandas import DataFrame, Series

from adjuftments_v2.application import db_session
from adjuftments_v2.config import DashboardConfig
from adjuftments_v2.schema import BudgetsTable, DashboardTable, ExpensesTable, MiscellaneousTable
from adjuftments_v2.utils import AdjuftmentsEncoder

logger = logging.getLogger(__name__)


class Dashboard(object):
    """
    Adjuftments Dashboarding
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
    def _categorize_expenses(cls, category: str, transaction: str) -> str:
        """
        Method to quickly categorize an expense using its category and transaction string

        Parameters
        ----------
        category: str
            Expense Category
        transaction: str
            Expense transaction string

        Returns
        -------
        str
        """
        if transaction.split("-")[0].strip().upper() == "REIMBURSEMENT":
            updated_category = "Reimbursement"
        elif category in ["Rent", "Mortgage"]:
            updated_category = "Housing"
        elif category in ["Savings", "Savings Spend"]:
            updated_category = "Savings"
        elif category in ["Income", "Interest"]:
            updated_category = "Income"
        elif category == "Adjustment":
            updated_category = "Adjustment"
        else:
            updated_category = "Expense"
        return updated_category

    @classmethod
    def _apply_checking_expense(cls, category: str, amount: float, transaction: str) -> float:
        """
        Method to handle an expenses impact on checking balance

        Parameters
        ----------
        category: str
            Expense category
        amount: float
            Expense amount
        transaction: str
            Expense transaction string

        Returns
        -------
        float
        """
        # If Category isn't Savings Spend or Interest...
        if category not in ["Savings Spend", "Interest"]:
            checking_impacted_amount = -amount
        # All Expenses Have an Impact on Checking Balance, Except for "Saving Spend"
        elif category == "Savings Spend":
            checking_impacted_amount = 0
        # Handle Interest Expenses
        elif category == "Interest":
            split_transaction = [item.lower().strip() for item in transaction.split("-")]
            # Handle a third transaction argument to dictate where interest goes
            if len(split_transaction) > 2:
                if "home" in split_transaction[2] or \
                        "house" in split_transaction[2] or \
                        "misc" in split_transaction[2] or \
                        "share" in split_transaction[2]:
                    checking_impacted_amount = 0
                # If the third transaction argument doesn't match up...
                else:
                    checking_impacted_amount = -amount
            # If the third transaction argument doesn't exist...
            else:
                checking_impacted_amount = -amount
        return checking_impacted_amount

    @classmethod
    def _classify_savings_expense(cls, transaction: str) -> str:
        """
        Direct a Savings Expense into a specific account

        Parameters
        ----------
        transaction

        Returns
        -------
        str
        """
        split_transaction = [item.lower().strip() for item in transaction.split("-")]
        if len(split_transaction) < 3:
            return "UNKNOWN"
        elif "home" in split_transaction[2] or "house" in split_transaction[2]:
            return "HOME"
        elif "misc" in split_transaction[2]:
            return "MISCELLANEOUS"
        elif "share" in split_transaction[2]:
            return "SHARED"
        else:
            return "UNKNOWN"

    @classmethod
    def _apply_savings_expense(cls, category: str, amount: float,
                               transaction: str) -> Dict[str, float]:
        """
        Method to handle an expenses impact on savings balances

        Parameters
        ----------
        category: str
            Expense category
        amount: float
            Expense amount
        transaction: str
            Expense transaction string

        Returns
        -------
        Dict[str, float]
        """
        # GET TRANSACTION TYPE AND VAR FOR NO IMPACT ON SAVINGS ACCOUNTS
        transaction_type = cls._classify_savings_expense(transaction=transaction)
        checking_transaction = dict(miscellaneous_savings=0,
                                    home_savings=0,
                                    shared_savings=0)
        # UPDATE THE AMOUNT IMPACT DEPENDING ON CATEGORY
        if category == "Savings Spend":
            updated_amount = -amount
            unknown_is_not_checking = False
        elif category == "Interest":
            updated_amount = -amount
            unknown_is_not_checking = True
        elif category == "Savings":
            updated_amount = amount
            unknown_is_not_checking = False
        else:
            return checking_transaction
        # CREATE A DICT THAT REPRESENTS IMPACTS ON DIFFERENT SAVINGS ACCOUNTS
        savings_expense_lookup = {
            "HOME": dict(miscellaneous_savings=0,
                         home_savings=updated_amount,
                         shared_savings=0),
            "MISCELLANEOUS": dict(miscellaneous_savings=updated_amount,
                                  home_savings=0,
                                  shared_savings=0),
            "SHARED": dict(miscellaneous_savings=0,
                           home_savings=0,
                           shared_savings=updated_amount),
            "UNKNOWN": dict(miscellaneous_savings=updated_amount,
                            home_savings=0,
                            shared_savings=0),
        }
        # PERFORM AN OVERRIDE FOR TRANSACTIONS THAT SHOULDN'T HAVE A SAVINGS IMPACT
        if unknown_is_not_checking is True:
            savings_expense_lookup["UNKNOWN"] = checking_transaction
        # RETURN THE LOOKUP VALUE
        return savings_expense_lookup[transaction_type]

    @classmethod
    def _balance_df(cls, dataframe: DataFrame, starting_checking_balance: float,
                    starting_miscellaneous_balance: float,
                    starting_home_balance: float,
                    starting_shared_balance: float) -> DataFrame:
        """
        Update the Expenses Dataframe with the Balances of each transaction on
        account balances.

        Parameters
        ----------
        dataframe: DataFrame
        starting_checking_balance
        starting_miscellaneous_balance
        starting_home_balance
        starting_shared_balance

        Returns
        -------
        DataFrame
        """
        updated_dataframe = dataframe.copy()
        # SORT DATAFRAME BY DATE
        updated_dataframe.sort_values(by=["date", "imported_at", "created_at"],
                                      ascending=True, inplace=True)
        updated_dataframe.reset_index(drop=True, inplace=True)
        # ADD A CATEGORY COLUMN
        updated_dataframe["expense_type"] = updated_dataframe.apply(
            lambda x: cls._categorize_expenses(category=x.category,
                                               transaction=x.transaction),
            axis=1)
        # APPLY THE AMOUNT COLUMNS FOR EFFECTS ON BALANCES
        updated_dataframe["checking_amount"] = updated_dataframe.apply(
            lambda x: cls._apply_checking_expense(category=x.category,
                                                  amount=x.amount,
                                                  transaction=x.transaction),
            axis=1)
        # APPLY SAVINGS BALANCES ACROSS A SERIES
        amount_columns = ["miscellaneous_amount", "home_amount", "shared_amount"]
        savings_columns = ["miscellaneous_savings", "home_savings", "shared_savings"]
        updated_dataframe[amount_columns] = updated_dataframe.apply(
            lambda x: cls._apply_savings_expense(category=x.category,
                                                 transaction=x.transaction,
                                                 amount=x.amount),
            axis=1).apply(Series)[savings_columns]
        # ADD STARTING BALANCES TO FIRST TRANSACTION
        updated_dataframe.at[0, "checking_amount"] += starting_checking_balance
        updated_dataframe.at[0, "miscellaneous_amount"] += starting_miscellaneous_balance
        updated_dataframe.at[0, "home_amount"] += starting_home_balance
        updated_dataframe.at[0, "shared_amount"] += starting_shared_balance
        # GET A RUNNING TOTAL OF BALANCES OVER TIME
        balance_columns = ["checking_balance", "miscellaneous_balance", "home_balance",
                           "shared_balance"]
        for balance_column in balance_columns:
            amount_string = balance_column.replace("balance", "amount")
            updated_dataframe[balance_column] = updated_dataframe[amount_string].cumsum()
        return updated_dataframe

    @classmethod
    def _get_account_balances(cls, dataframe: DataFrame) -> Dict[str, str]:
        """
        Given an updated Dataframe, grab its final rows and package them as a dictionary

        Parameters
        ----------
        dataframe: DataFrame
            Output from Dashboard.balance_df()

        Returns
        -------
        Dict[str, str]
            A dictionary containing account balances
        """
        balance_columns = ["checking_balance", "miscellaneous_balance",
                           "home_balance", "shared_balance"]
        returned_values = dataframe.iloc[[-1]][balance_columns].to_dict(orient="records")[0]
        savings_values = returned_values.copy()
        savings_values.pop("checking_balance")
        net_worth = sum(returned_values.values())
        total_savings = sum(savings_values.values())
        returned_values["net_worth"] = net_worth
        returned_values["total_savings"] = total_savings
        return returned_values

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
        current_months_data

        Returns
        -------

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
    def _get_monthly_totals(cls, dataframe: DataFrame):
        """
        Get Monthly Summary from Expense Dataframe
        Parameters
        ----------
        dataframe

        Returns
        -------

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
        prepared_dict["monthly_income"] = -updated_categories.get("Income", 0.0)
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
        elif pay_check_count == 2:
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
            Expenses Dataframe

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
    def _get_dashboard_dict(cls, dataframe: DataFrame) -> dict:
        """
        Run the full thing

        Parameters
        ----------
        dataframe

        Returns
        -------
        dict
        """
        miscellaneous_dict = cls._get_miscellaneous_data()
        balanced_data = cls._balance_df(
            dataframe=dataframe,
            starting_checking_balance=float(miscellaneous_dict["Starting Checking Balance"]),
            starting_miscellaneous_balance=float(miscellaneous_dict["Starting Savings Balance"]),
            starting_home_balance=float(miscellaneous_dict["Starting House Balance"]),
            starting_shared_balance=float(miscellaneous_dict["Starting Shared Balance"])
        )
        account_balances = cls._get_account_balances(dataframe=balanced_data)
        monthly_totals = cls._get_monthly_totals(dataframe=balanced_data)
        finance_dict = dict(**account_balances, **monthly_totals)
        finance_dict["amount_to_save"] = cls._get_amount_to_save(dataframe=balanced_data,
                                                                 finance_dict=finance_dict)
        budget_dict = cls._get_budget_based_calculations(finance_dict=finance_dict)
        update_dict = cls._get_final_dashboard_updates()
        prepared_dashboard_dict = dict(**finance_dict, **budget_dict, **update_dict)
        return prepared_dashboard_dict

    @staticmethod
    def run_dashboard(dataframe: DataFrame,
                      splitwise_balance: Optional[float] = None) -> List[dict]:
        """
        Run the whole gosh darn thing

        Parameters
        ----------
        dataframe : DataFrame
        splitwise_balance : bool
            Optional Updated Splitwise Balance
        Returns
        -------
        List[dict]
            Update Manifest
        """
        prepared_dashboard_dict = Dashboard._get_dashboard_dict(dataframe=dataframe)
        if splitwise_balance is not None:
            prepared_dashboard_dict["splitwise_balance"] = splitwise_balance
        processed_dashboard_dict = Dashboard._process_dashboard_dict(
            dashboard_dict=prepared_dashboard_dict)
        db_update_manifest = Dashboard._unload_dashboard_dict_to_manifest(
            dashboard_dict=processed_dashboard_dict)
        Dashboard._unload_manifest_to_database(manifest=db_update_manifest)
        return db_update_manifest

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

        Parameters
        ----------
        dashboard_dict: dict
            Existing Dashboard Dict

        Returns
        -------

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

        Parameters
        ----------
        dashboard_dict: dict
            Existing Dashboard Dict

        Returns
        -------

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
                if existing_row.value != value:
                    manifest.append(dict(id=existing_row.id, measure=existing_row.measure,
                                         value=value))
            except KeyError:
                pass
        return manifest

    @classmethod
    def _unload_manifest_to_database(cls, manifest: List[dict]) -> None:
        """
        Unload a prepared manifest into the Database

        Parameters
        ----------
        manifest: Update manifest

        Returns
        -------
        None
        """
        for update_manifest in manifest:
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

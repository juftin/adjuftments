#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Endpoints for Accessing Financial Data and Services
"""

from datetime import datetime
from json import loads
import logging
from typing import List, Union

from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from flask import abort, Blueprint, jsonify, render_template, request, Response
from flask_login import login_required
from pandas import DataFrame
from requests.api import get
from sqlalchemy import asc, Table

from adjuftments import Airtable, Dashboard
from adjuftments.config import AirtableConfig, APIEndpoints, DOT_ENV_FILE_PATH
from adjuftments.schema import AccountsTable, DashboardTable, ExpensesTable
from adjuftments.utils import AdjuftmentsEncoder

load_dotenv(DOT_ENV_FILE_PATH, override=True)
logger = logging.getLogger(__name__)

finance = Blueprint(name="finance", import_name=__name__)


@finance.route(rule=APIEndpoints.EXPENSE_CATEGORIES, methods=["GET"])
@login_required
def get_current_months_expenses() -> Response:
    """
    Return data on the current mont's spending grouped by category

    Returns
    -------
    Response
    """
    adjuftments_table = ExpensesTable
    # DEFINE DATE WINDOWS
    current_time = datetime.now()
    month_from_now = current_time + relativedelta(months=1)
    next_month = month_from_now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # GET DATA
    date_filter = adjuftments_table.date.between(this_month, next_month)
    response: List[Table] = adjuftments_table.query.filter(date_filter).all()
    if response is None:
        abort(status=404, description=f"Something went wrong fetching this months data")
    elif len(response) == 0:
        return jsonify(dict())
    response_array = [result.to_dict() for result in response]
    current_categories = DataFrame(response_array).groupby(["category"])["amount"].sum().to_dict()
    excluded_rows = ["Rent", "Mortgage", "Income", "Savings", "Savings Spend", "Interest"]
    for row in excluded_rows:
        try:
            current_categories.pop(row)
        except KeyError:
            pass
    total_sum = sum(current_categories.values())
    formatted_response = dict()
    for category, amount in current_categories.items():
        formatted_response[category] = dict(amount=amount, percent_of_total=amount / total_sum)
    return jsonify(formatted_response)


@finance.route(rule=f"{APIEndpoints.STOCK_TICKER_API}/<ticker>", methods=["GET"])
@login_required
def get_stock_ticker(ticker: str) -> Response:
    """
    Get Stock Prices

    Parameters
    ----------
    ticker: str
    """
    url_response = get(url=f"https://query1.finance.yahoo.com/v7/finance/options/{ticker}")
    response = loads(url_response.content)
    stocks_response = dict(
        symbol=response["optionChain"]["result"][0]["quote"]["symbol"],
        display_name=response["optionChain"]["result"][0]["quote"]["displayName"],
        price=response["optionChain"]["result"][0]["quote"]["regularMarketPrice"])
    return jsonify(stocks_response)


@finance.route(rule=APIEndpoints.DASHBOARD_GENERATOR, methods=["POST"])
@login_required
def refresh_dashboard() -> Union[Response, str]:
    """
    Interact with the Adjuftments Dashboard.

    - GET: Returns the Dashboard table as a rendered HTML Template
    - POST: Refreshes the Dashboard, returning the new data

    Returns
    -------
    Response
    """
    airtable_object = Airtable(base=AirtableConfig.AIRTABLE_BASE,
                               table="dashboard")

    logger.info("Retrieving Data for Dashboard")
    clean_data_filter = dict(imported=True, delete=False)
    response = ExpensesTable.query.filter_by(**clean_data_filter).limit(None)
    response_array = [result.to_dict() for result in response]
    cleaned_response_array = AdjuftmentsEncoder.parse_object(response_array)
    logger.info("Data retrieved, converting data to DataFrame")
    df = Airtable.expenses_as_df(expense_array=cleaned_response_array)
    request_json = request.get_json()
    splitwise_balance = request_json.get("splitwise_balance", None)
    updated_data = request_json.get("updated_data", False)
    dashboard_manifest = Dashboard.run_dashboard(dataframe=df, splitwise_balance=splitwise_balance,
                                                 updated_data=updated_data)
    if updated_data is True:
        accounts_data = AccountsTable.query.all()
        for account in accounts_data:
            account_airtable_obj = Airtable(base=AirtableConfig.AIRTABLE_BASE,
                                            table="accounts")
            account_airtable_obj.update(record_id=account.id,
                                        fields=dict(Balance=float(account.balance)))

    logger.info(f"{len(dashboard_manifest)} dashboard records to update in Airtable")
    for manifest_record in dashboard_manifest:
        update_fields = dict(Value=manifest_record["value"])
        airtable_object.update(record_id=manifest_record["id"],
                               fields=update_fields,
                               typecast=True)
    logger.info("Dashboard Refresh Complete")
    all_dashboard_data = DashboardTable.query.limit(None)
    response_array = [result.to_dict() for result in all_dashboard_data]
    response_dict = dict(manifest=dashboard_manifest,
                         dashboard=response_array)
    return jsonify(response_dict)


@finance.route(rule=APIEndpoints.DASHBOARD_HTML, methods=["GET"])
def get_dashboard_html() -> Union[Response, str]:
    """
    Returns the Dashboard table as a rendered HTML Template

    Returns
    -------
    Response
    """
    logger.critical("dfsdfgsdfa")
    dashboard_data = DashboardTable.query. \
        with_entities(DashboardTable.measure, DashboardTable.value). \
        order_by(asc(DashboardTable.ordinal_position)). \
        all()
    return render_template("dashboard.html", items=dashboard_data)

#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
FLASK API CONFIGURATION
"""

from datetime import datetime, timedelta
from json import loads
import logging
from os import getenv
from typing import List, Optional, Union
from urllib.parse import urljoin

from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from flask import abort, jsonify, request, Response
from flask_login import login_required
from flask_sqlalchemy import Model
from pandas import DataFrame
from requests import delete, get, post
from sqlalchemy import func

from adjuftments_v2 import Airtable, Dashboard, Splitwise
from adjuftments_v2.application import app, db, login_manager
from adjuftments_v2.config import (AirtableConfig, APIEndpoints, DOT_ENV_FILE_PATH,
                                   FlaskDefaultConfig, SplitwiseConfig)
from adjuftments_v2.models import DashboardTable, ExpensesTable, MODEL_FINDER, UsersTable
from adjuftments_v2.utils import AdjuftmentsEncoder

load_dotenv(DOT_ENV_FILE_PATH, override=True)
logger = logging.getLogger(__name__)

logging.basicConfig(format="%(asctime)s [%(levelname)8s]: %(message)s [%(name)s]",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)


@login_manager.request_loader
def load_user_from_request(flask_request: request) -> Optional[Model]:
    """
    Assert a Header's token Auth is in the users table

    Parameters
    ----------
    flask_request

    Returns
    -------
    Optional[Model]
    """
    api_token = flask_request.headers.get("Authorization")
    if api_token is not None:
        api_token = api_token.replace('Bearer ', '', 1)
        user = UsersTable.query.filter_by(api_token=api_token).first()
        if user is not None:
            return user
    # finally, return None if both methods did not login the user
    return None


@app.route(rule=APIEndpoints.ADMIN_USERS, methods=["POST"])
def clean_start_system_users() -> Response:
    """
    This is the lone API Endpoint that doesn't require
    authentication, since it can only be called when the Admin Users
    Table is empty, (and no other endpoints will Auth.)
    """
    error_description = ("The database isn't in a state for this "
                         f"endpoint to work: {APIEndpoints.ADMIN_USERS}")
    clean_start_param = request.json.get("clean_start")
    if clean_start_param is True:
        all_users = UsersTable.query.all()
        if len(all_users) != 0:
            abort(status=500, description=error_description)
        adjuftments_user = UsersTable(username=FlaskDefaultConfig.DATABASE_USERNAME)
        adjuftments_user.set_api_token(api_token=FlaskDefaultConfig.API_TOKEN)
        db.session.merge(adjuftments_user)
        db.session.commit()
        return jsonify(adjuftments_user.to_dict())
    else:
        abort(status=500, description=error_description)


@app.route(rule=APIEndpoints.ADMIN_USERS, methods=["GET"])
@login_required
def interact_with_system_users() -> Response:
    all_users = UsersTable.query.all()
    prepared_users = [user.to_dict() for user in all_users]
    return jsonify(prepared_users)


@app.route(rule=f"{APIEndpoints.AIRTABLE_BASE}/<table>", methods=["GET", "POST"])
@login_required
def interact_with_airtable_table(table: str) -> Response:
    """
    Interact with an Airtable table depending on the HTTP Request type.
    - GET requests will return all data (and additional filters can be passsed).
    - POST requests will create an Airtable record, given that the proper fields are passed as JSON

    Returns
    -------

    """
    parameters = request.args.to_dict()
    optional_airtable_base = parameters.pop("airtable_base", None)
    if request.method == "GET" and optional_airtable_base is not None:
        airtable_base = optional_airtable_base
    else:
        airtable_base = AirtableConfig.AIRTABLE_BASE
    airtable_object = Airtable(base=airtable_base,
                               table=table)
    # GET DATA
    if request.method == "GET":
        # OR({Imported}=FALSE(), {Delete}=True())
        records = airtable_object.get_all(**parameters)
        record_array = [airtable_object.process_airtable_response(table=table, response=record) for
                        record in records]
        return jsonify(record_array)
    # CREATE DATA
    elif request.method == "POST":
        insert_json = airtable_object.get_column_mapping_json(table=table,
                                                              airtable_dict=request.get_json())
        record_response = airtable_object.insert(fields=insert_json, typecast=True)
        normalized_response = airtable_object.process_airtable_response(table=table,
                                                                        response=record_response)
        return jsonify(normalized_response)


@app.route(rule=f"{APIEndpoints.AIRTABLE_BASE}/<table>/<record_id>",
           methods=["GET", "POST", "DELETE"])
@login_required
def interact_with_airtable_record(table: str, record_id: str) -> Response:
    """

    Parameters
    ----------
    record_id

    Returns
    -------

    """
    parameters = request.args.to_dict()
    optional_airtable_base = parameters.pop("airtable_base", None)
    if request.method == "GET" and optional_airtable_base is not None:
        airtable_base = optional_airtable_base
    else:
        airtable_base = AirtableConfig.AIRTABLE_BASE
    airtable_object = Airtable(base=airtable_base,
                               table=table)
    # GET DATA
    if request.method == "GET":
        record = airtable_object.get(record_id=record_id)
        flattened_row = airtable_object.process_airtable_response(table=table, response=record)
        return jsonify(flattened_row)
    # UPDATE DATA
    elif request.method == "POST":
        update_json = airtable_object.get_column_mapping_json(table=table,
                                                              airtable_dict=request.get_json())
        record_response = airtable_object.update(record_id=record_id,
                                                 fields=update_json,
                                                 typecast=True)
        normalized_response = airtable_object.process_airtable_response(table=table,
                                                                        response=record_response)
        return jsonify(normalized_response)
    # DELETE DATA
    elif request.method == "DELETE":
        record_response = airtable_object.delete(record_id=record_id)
        return jsonify(record_response)


@app.route(rule=APIEndpoints.SPLITWISE_EXPENSES, methods=["GET", "POST"])
@login_required
def interact_with_splitwise_expenses() -> Response:
    """
    Interact with an Splitwise table depending on the HTTP Request type.
    - GET requests will return all data (and additional filters can be passsed).
    - POST requests will create an Airtable record, given that the proper fields are passed as JSON

    Returns
    -------

    """
    splitwise_obj = Splitwise(consumer_key=SplitwiseConfig.SPLITWISE_CONSUMER_KEY,
                              consumer_secret=SplitwiseConfig.SPLITWISE_CONSUMER_SECRET,
                              access_token=SplitwiseConfig.SPLITWISE_ACCESS_TOKEN,
                              financial_partner=SplitwiseConfig.SPLITWISE_FINANCIAL_PARTNER)
    # GET DATA
    if request.method == "GET":
        records = splitwise_obj.get_expenses(**request.args.to_dict())
        return jsonify(records)
    # CREATE DATA
    elif request.method == "POST":
        request_json = request.get_json()
        response = splitwise_obj.create_self_paid_expense(amount=request_json["cost"],
                                                          description=request_json["description"])
        return jsonify(response)


@app.route(rule=f"{APIEndpoints.SPLITWISE_EXPENSES}/<record_id>", methods=["GET", "DELETE"])
@login_required
def interact_with_splitwise_record(record_id: int) -> Response:
    """
    Interact with an Splitwise table depending on the HTTP Request type.
    - GET requests will return all data (and additional filters can be passsed).
    - POST requests will create an Airtable record, given that the proper fields are passed as JSON

    Returns
    -------

    """
    splitwise_obj = Splitwise(consumer_key=SplitwiseConfig.SPLITWISE_CONSUMER_KEY,
                              consumer_secret=SplitwiseConfig.SPLITWISE_CONSUMER_SECRET,
                              access_token=SplitwiseConfig.SPLITWISE_ACCESS_TOKEN,
                              financial_partner=SplitwiseConfig.SPLITWISE_FINANCIAL_PARTNER)
    # GET DATA
    if request.method == "GET":
        record = splitwise_obj.getExpense(id=record_id)
        formatted_record = splitwise_obj.process_expense(expense=record)
        return jsonify(formatted_record)
    # DELETE THE DATA
    elif request.method == "DELETE":
        delete_success, delete_errors = splitwise_obj.deleteExpense(id=record_id)
        if delete_success is not True:
            abort(status=404, description=delete_errors)
        else:
            return jsonify(delete_success)


@app.route(rule=APIEndpoints.SPLITWISE_BALANCE, methods=["GET"])
@login_required
def get_splitwise_balance() -> Response:
    """
    Retrieve Current Balance with Splitwise Partner
    """
    splitwise_obj = Splitwise(consumer_key=SplitwiseConfig.SPLITWISE_CONSUMER_KEY,
                              consumer_secret=SplitwiseConfig.SPLITWISE_CONSUMER_SECRET,
                              access_token=SplitwiseConfig.SPLITWISE_ACCESS_TOKEN,
                              financial_partner=SplitwiseConfig.SPLITWISE_FINANCIAL_PARTNER)
    # GET DATA
    if request.method == "GET":
        balance = splitwise_obj.get_balance()
        formatted_record = dict(balance=balance)
        return jsonify(formatted_record)


@app.route(rule=f"{APIEndpoints.ADJUFTMENTS_BASE}/<table>", methods=["GET", "POST"])
@login_required
def interact_with_adjuftments_table(table: str) -> Response:
    """
    Interact with an Adjuftments SQL Table
    - GET requests will return all data (and additional filters can be passsed).
    - POST requests will create an Airtable record, given that the proper fields are passed as JSON

    Returns
    -------

    """
    adjuftments_table = MODEL_FINDER.get(table, None)
    if adjuftments_table is None:
        abort(status=500,
              description=("Adjuftments table does not exist or "
                           f"is not externally accessible: {table}"))
    # GET DATA
    if request.method == "GET":
        request_args = request.args.to_dict()
        # CHECK FOR LIMIT PARAMETER
        try:
            limit = request_args.pop("limit")
        except KeyError:
            limit = None
        # GET THE DATABASE RESPONSE
        response: List[Model] = adjuftments_table.query.filter_by(**request_args).limit(limit)
        # HANDLE ERRORS
        if response is None:
            abort(status=404, description=f"Something went wrong fetching that data: ({table})")
        # FLATTEN DATA AND RETURN IT
        response_array = [result.to_dict() for result in response]
        return jsonify(response_array)
    # INSERT DATA
    elif request.method == "POST":
        request_json = request.get_json()
        new_record = adjuftments_table(**request_json)
        db.session.merge(new_record)
        db.session.commit()
        logger.info(f"DB Record Inserted: {adjuftments_table.__tablename__} - {new_record.id}")
        return jsonify(new_record.to_dict())


@app.route(rule=APIEndpoints.EXPENSE_CATEGORIES, methods=["GET"])
@login_required
def get_current_months_expenses() -> Response:
    """
    Interact with an Adjuftments SQL Table
    - GET requests will return all data (and additional filters can be passsed).
    - POST requests will create an Airtable record, given that the proper fields are passed as JSON

    Returns
    -------

    """
    adjuftments_table = ExpensesTable
    # DEFINE DATE WINDOWS
    current_time = datetime.now()
    month_from_now = current_time + relativedelta(months=1)
    next_month = month_from_now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month = current_time.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # GET DATA
    date_filter = adjuftments_table.date.between(this_month, next_month)
    response: List[Model] = adjuftments_table.query.filter(date_filter).all()
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


@app.route(rule=f"{APIEndpoints.ADJUFTMENTS_BASE}/<table>/<key>", methods=["GET", "POST", "DELETE"])
@login_required
def interact_with_adjuftments_record(table: str, key: Union[str, int]) -> Response:
    """
    Retrieve a Single Record by its primary key

    Interact with an SAdjuftments SQL Table
    - GET requests will return all data (and additional filters can be passsed).
    - POST requests will create an Airtable record, given that the proper fields are passed as JSON

    Returns
    -------

    """
    adjuftments_table = MODEL_FINDER.get(table, None)
    if adjuftments_table is None:
        abort(status=500,
              description=("Adjuftments table does not exist or "
                           f"is not externally accessible: {table}"))
    selected_row: Model = adjuftments_table.query.get(key)
    # GET THE DATA
    if request.method == "GET":
        if selected_row is None:
            error_message = f"GET: Row not found: ({table}) ({key})"
            logger.error(error_message)
            abort(status=404, description=error_message)
        else:
            formatted_response = selected_row.to_dict()
            return jsonify(formatted_response)
    # UPDATE THE DATA
    elif request.method == "POST":
        if selected_row is None:
            error_message = f"UPDATE: Row not Found: {table} - {key}"
            logger.error(error_message)
            abort(status=404, description=error_message)
        else:
            row_args = request.args.to_dict()
            row_args["id"] = key
            updated_row = adjuftments_table(**row_args)
            db.session.merge(updated_row)
            db.session.commit()
            logger.info(f"UPDATE: Row updated: {table} - {key}")
            formatted_response = updated_row.to_dict()
            return jsonify(formatted_response)
    # DELETE THE DATA
    elif request.method == "DELETE":
        deleted_row = adjuftments_table.query.get(key)
        if selected_row is None:
            error_message = f"DELETE: Row not Found: {table} - {key}"
            logger.error(error_message)
            abort(status=404, description=error_message)
        else:
            db.session.delete(deleted_row)
            db.session.commit()
            logger.info(f"DELETE: Row Deleted: {table} - {key}")
            formatted_response = selected_row.to_dict()
            return jsonify(formatted_response)


@app.route(rule=f"{APIEndpoints.STOCK_TICKER_API}/<ticker>", methods=["GET"])
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


@app.route(rule=APIEndpoints.DASHBOARD_GENERATOR, methods=["POST"])
@login_required
def refresh_dashboard() -> Response:
    """
    Refresh Adjuftments Dashboard
    """
    airtable_object = Airtable(base=AirtableConfig.AIRTABLE_BASE,
                               table="dashboard")

    logger.info("Retrieving Data for Dashboard")
    clean_data_filter = dict(imported=True, delete=False)
    adjuftments_table = ExpensesTable
    response = adjuftments_table.query.filter_by(**clean_data_filter).limit(None)
    response_array = [result.to_dict() for result in response]
    cleaned_response_array = AdjuftmentsEncoder.parse_object(response_array)
    logger.info("Data retrieved, converting data to DataFrame")
    df = Airtable.expenses_as_df(expense_array=cleaned_response_array)
    request_json = request.get_json()
    splitwise_balance = request_json.get("splitwise_balance", None)
    dashboard_manifest = Dashboard.run_dashboard(dataframe=df, splitwise_balance=splitwise_balance)

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


@app.route(rule=APIEndpoints.ADMIN_DATABASE_BUILD, methods=["POST"])
def prepare_database() -> Response:
    """
    Refresh Adjuftments Dashboard

    Parameters
    ----------
    ticker: str
    """

    from adjuftments_v2.models import ALL_TABLES

    logger.info(f"Preparing Database: {len(ALL_TABLES)} table(s)")
    if not db.engine.dialect.has_schema(db.engine, "adjuftments"):
        db.engine.execute("CREATE SCHEMA adjuftments;")
    request_json = request.get_json()
    drop_all = request_json.get("drop_all", False)
    if drop_all is True:
        db.drop_all()
    db.create_all()
    return jsonify(True)


@app.route(rule=APIEndpoints.SPLITWISE_UPDATED_AT, methods=["GET"])
@login_required
def get_splitwise_updated_timestamp() -> Response:
    """
    Retrieve Max Timestamp from Splitwise (for ETL)
    """
    max_splitwise_timestamp = get_max_date(table="splitwise",
                                           date_column="updated_at",
                                           replace_none=True)
    new_data_updated_after = max_splitwise_timestamp + timedelta(microseconds=1)
    params = dict(updated_after=new_data_updated_after)
    return jsonify(params)


@app.route(rule=APIEndpoints.IMAGES_ENDPOINT, methods=["POST"])
@login_required
def upload_imgur_image() -> Response:
    """
    Retrieve Max Timestamp from Splitwise (for ETL)
    """
    imgur_api_url = "https://api.imgur.com/3/image"
    headers = dict(Authorization=f"Client-ID {getenv('IMGUR_CLIENT_ID')}")
    response = post(url=imgur_api_url,
                    headers=headers,
                    data=request.get_data(),
                    files=list())
    if response.status_code != 200:
        logger.error(response.text)
        abort(status=response.status_code, description=response.text)
    return jsonify(loads(response.content))


@app.route(rule=f"{APIEndpoints.IMAGES_ENDPOINT}/<image_delete_hash>", methods=["DELETE"])
@login_required
def delete_imgur_image(image_delete_hash: str) -> Response:
    """
    Retrieve Max Timestamp from Splitwise (for ETL)
    """
    imgur_api_url = urljoin("https://api.imgur.com/3/image", image_delete_hash)
    headers = dict(Authorization=f"Client-ID {getenv('IMGUR_CLIENT_ID')}")
    response = delete(imgur_api_url, headers=headers,
                      data=dict(), files=dict())
    if response.status_code != 200:
        abort(status=response.status_code, description=response.text)
    return jsonify(loads(response.content))


@app.route(rule=APIEndpoints.HEALTHCHECK, methods=["GET"])
def check_api_health() -> Response:
    """
    Retrieve Max Timestamp from Splitwise (for ETL)
    """
    return jsonify(True)


def get_max_date(table: str, date_column: str,
                 replace_none: bool = False) -> datetime:
    """
    Retrieve a Max Date Column from Table

    Parameters
    ----------
    table: str
        DB Table
    date_column: str
        column name
    replace_none: bool
        Whether to replace a very old timestamp instead of None

    Returns
    -------
    datetime
    """
    database_table = MODEL_FINDER.get(table, None)
    if database_table is None:
        abort(status=500, description=f"Table doesn't exist: {table}")
    database_column = getattr(database_table, date_column)
    response = db.session.query(func.max(database_column)).first()
    if replace_none is True and response[0] is None:
        response = (datetime(year=1975, month=1, day=1), None)
    max_value = response[0]
    return max_value

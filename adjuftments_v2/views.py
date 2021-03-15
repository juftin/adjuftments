#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from json import loads
import logging
from os import getenv
from typing import List, Optional, Union

from flask import abort, jsonify, request, Response
from flask_login import login_required
from flask_sqlalchemy import Model
from requests import get

from adjuftments_v2 import Airtable, Splitwise
from adjuftments_v2.application import app, db, login_manager
from adjuftments_v2.config import AirtableConfig, APIEndpoints, SplitwiseConfig
from adjuftments_v2.models import MODEL_FINDER

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
        user = MODEL_FINDER["users"].query.filter_by(api_token=api_token).first()
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
        all_users = MODEL_FINDER["users"].query.all()
        if len(all_users) != 0:
            abort(status=500, description=error_description)
        juftin_user = MODEL_FINDER["users"](username="juftin")
        juftin_user.set_api_token(api_token=getenv("DATABASE_PASSWORD"))
        db.session.merge(juftin_user)
        db.session.commit()
        return jsonify(juftin_user.to_dict())
    else:
        abort(status=500, description=error_description)


@app.route(rule=APIEndpoints.ADMIN_USERS, methods=["GET"])
@login_required
def interact_with_system_users() -> Response:
    all_users = MODEL_FINDER["users"].query.all()
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
    airtable_object = Airtable(base=AirtableConfig.AIRTABLE_BASE,
                               table=table)
    # GET DATA
    if request.method == "GET":
        # OR({Imported}=FALSE(), {Delete}=True())
        records = airtable_object.get_all(**request.args.to_dict())
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
    airtable_object = Airtable(base="app6gz8Qeg6CHxpam",
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
    adjuftments_table = MODEL_FINDER[table]
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
    adjuftments_table = MODEL_FINDER[table]
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

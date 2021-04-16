#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Endpoints for Accessing Splitwise
"""

import logging

from dotenv import load_dotenv
from flask import abort, Blueprint, jsonify, request, Response
from flask_login import login_required

from adjuftments import Splitwise
from adjuftments.config import APIEndpoints, DOT_ENV_FILE_PATH, SplitwiseConfig

load_dotenv(DOT_ENV_FILE_PATH, override=True)
logger = logging.getLogger(__name__)

splitwise = Blueprint(name="splitwise", import_name=__name__)


@splitwise.route(rule=APIEndpoints.SPLITWISE_EXPENSES, methods=["GET", "POST"])
@login_required
def interact_with_splitwise_expenses() -> Response:
    """
    Interact with an Splitwise expenses depending on the HTTP Request type.

    - GET requests will return all expenses (and additional filters can be passsed).
    - POST requests will create a Splitwise expense, given that the proper fields are passed as JSON

    Returns
    -------
    Response
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


@splitwise.route(rule=f"{APIEndpoints.SPLITWISE_EXPENSES}/<record_id>",
                 methods=["GET", "DELETE"])
@login_required
def interact_with_splitwise_record(record_id: int) -> Response:
    """
    Interact with an Splitwise records depending on the HTTP Request type.

    - GET requests will return an expenses data
    - DELETE requests will delete a Splitwise expense

    Returns
    -------
    Response
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


@splitwise.route(rule=APIEndpoints.SPLITWISE_BALANCE, methods=["GET"])
@login_required
def get_splitwise_balance() -> Response:
    """
    Retrieve Current Balance with Splitwise Partner

    Returns
    -------
    Response
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

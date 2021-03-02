#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

import logging

from flask import jsonify, request, Response

from adjuftments_v2 import Airtable, app, Splitwise
from adjuftments_v2.config import AirtableConfig, SplitwiseConfig

logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s [%(levelname)8s]: %(message)s [%(name)s]",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO)


@app.route(rule='/api/1.0/airtable/<table>', methods=["GET", "POST"])
def interact_with_airtable_table(table: str) -> Response:
    """
    Interact with an Airtable table depending on the HTTP Request type.
    - GET requests will return all data (and additional filters can be passsed).
    - POST requests will create an Airtable record, given that the proper fields are passed as JSON

    Returns
    -------

    """
    airtableExpenses = Airtable(base=AirtableConfig.AIRTABLE_BASE,
                                table=table)
    if request.method == "GET":
        # OR({Imported}=FALSE(), {Delete}=True())
        logger.info(request.args.to_dict())
        records = airtableExpenses.get_all(**request.args.to_dict())
        return jsonify(records)
    # elif request.method == "POST":
    #     request_data = request.json
    #     airtable_response = airtableExpenses.insert(fields=request.json, typecast=True)
    #     app.logger.info(airtable_response)
    #     return jsonify(airtable_response)


@app.route(rule="/api/1.0/airtable/<table>/<record_id>", methods=["GET", "POST"])
def interact_with_airtable_record(table: str, record_id: str) -> Response:
    """

    Parameters
    ----------
    record_id

    Returns
    -------

    """
    airtable_expenses = Airtable(base="app6gz8Qeg6CHxpam",
                                 table=table)
    if request.method == "GET":
        record = airtable_expenses.get(record_id=record_id)
        return jsonify(record)


@app.route(rule='/api/1.0/splitwise/expenses', methods=["GET", "POST"])
def interact_with_splitwise_expenses() -> Response:
    """
    Interact with an Splitwise table depending on the HTTP Request type.
    - GET requests will return all data (and additional filters can be passsed).
    - POST requests will create an Airtable record, given that the proper fields are passed as JSON

    Returns
    -------

    """
    splitwiseObj = Splitwise(consumer_key=SplitwiseConfig.SPLITWISE_CONSUMER_KEY,
                             consumer_secret=SplitwiseConfig.SPLITWISE_CONSUMER_SECRET,
                             access_token=SplitwiseConfig.SPLITWISE_ACCESS_TOKEN,
                             significant_other=SplitwiseConfig.SPLITWISE_SIGNIFICANT_OTHER)

    if request.method == "GET":
        # OR({Imported}=FALSE(), {Delete}=True())
        logger.info(request.args.to_dict())
        records = splitwiseObj.get_expenses(**request.args.to_dict())
        return jsonify(records)


@app.route(rule='/api/1.0/splitwise/expenses/<record_id>', methods=["GET", "POST"])
def interact_with_splitwise_record(record_id: int) -> Response:
    """
    Interact with an Splitwise table depending on the HTTP Request type.
    - GET requests will return all data (and additional filters can be passsed).
    - POST requests will create an Airtable record, given that the proper fields are passed as JSON

    Returns
    -------

    """
    splitwiseObj = Splitwise(consumer_key=SplitwiseConfig.SPLITWISE_CONSUMER_KEY,
                             consumer_secret=SplitwiseConfig.SPLITWISE_CONSUMER_SECRET,
                             access_token=SplitwiseConfig.SPLITWISE_ACCESS_TOKEN,
                             significant_other=SplitwiseConfig.SPLITWISE_SIGNIFICANT_OTHER)

    if request.method == "GET":
        # OR({Imported}=FALSE(), {Delete}=True())
        logger.info(request.args.to_dict())
        record = splitwiseObj.getExpense(id=record_id)
        formatted_record = splitwiseObj.process_expense(expense=record)
        return jsonify(formatted_record)

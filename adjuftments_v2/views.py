#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from flask import jsonify, request, Response

from adjuftments_v2 import Airtable, app


@app.route(rule='/api/1.0/airtable/<table>/', methods=["GET", "POST"])
def interact_with_airtable_table(table: str) -> Response:
    """
    Interact with an Airtable table depending on the HTTP Request type.
    - GET requests will return all data (and additional filters can be passsed).
    - POST requests will create an Airtable record, given that the proper fields are passed as JSON

    Returns
    -------

    """
    airtable_expenses = Airtable(base="app6gz8Qeg6CHxpam",
                                 table=table)
    if request.method == "GET":
        records = airtable_expenses.get_all(**request.args.to_dict())
        return jsonify(records)
    elif request.method == "POST":
        request_data = request.json
        airtable_response = airtable_expenses.insert(fields=request.json, typecast=True)
        app.logger.info(airtable_response)
        return jsonify(airtable_response)


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

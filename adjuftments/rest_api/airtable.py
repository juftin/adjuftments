#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Endpoints for Accessing Splitwise
"""

import logging

from dotenv import load_dotenv
from flask import Blueprint, jsonify, request, Response
from flask_login import login_required

from adjuftments import Airtable
from adjuftments.config import AirtableConfig, APIEndpoints, DOT_ENV_FILE_PATH

load_dotenv(DOT_ENV_FILE_PATH, override=True)
logger = logging.getLogger(__name__)

airtable = Blueprint(name="airtable", import_name=__name__)


@airtable.route(rule=f"{APIEndpoints.AIRTABLE_BASE}/<table>", methods=["GET", "POST"])
@login_required
def interact_with_airtable_table(table: str) -> Response:
    """
    Interact with an Airtable table depending on the HTTP Request type.

    - GET requests will return all data (and additional filters can be passsed).
    - POST requests will create an Airtable record, given that the proper fields are passed as JSON

    Returns
    -------
    Response
    """
    parameters = request.args.to_dict()
    optional_airtable_base = parameters.pop("airtable_base", None)
    if optional_airtable_base is not None:
        airtable_base = optional_airtable_base
    else:
        airtable_base = AirtableConfig.AIRTABLE_BASE
    airtable_object = Airtable(base=airtable_base,
                               table=table)
    if request.method == "GET":
        records = airtable_object.get_all(**parameters)
        record_array = [airtable_object.process_airtable_response(table=table, response=record) for
                        record in records]
        return jsonify(record_array)
    elif request.method == "POST":
        insert_json = airtable_object.get_column_mapping_json(table=table,
                                                              airtable_dict=request.get_json())
        record_response = airtable_object.insert(fields=insert_json, typecast=True)
        normalized_response = airtable_object.process_airtable_response(table=table,
                                                                        response=record_response)
        return jsonify(normalized_response)


@airtable.route(rule=f"{APIEndpoints.AIRTABLE_BASE}/<table>/<record_id>",
                methods=["GET", "POST", "DELETE"])
@login_required
def interact_with_airtable_record(table: str, record_id: str) -> Response:
    """
    Interact with a particular record in Airtable

    Parameters
    ----------
    table: str
        Airtable Table
    record_id: str
        Airtable Record ID

    Returns
    -------
    Response
    """
    parameters = request.args.to_dict()
    optional_airtable_base = parameters.pop("airtable_base", None)
    if optional_airtable_base is not None:
        airtable_base = optional_airtable_base
    else:
        airtable_base = AirtableConfig.AIRTABLE_BASE
    airtable_object = Airtable(base=airtable_base,
                               table=table)
    if request.method == "GET":
        record = airtable_object.get(record_id=record_id)
        flattened_row = airtable_object.process_airtable_response(table=table, response=record)
        return jsonify(flattened_row)
    elif request.method == "POST":
        update_json = airtable_object.get_column_mapping_json(table=table,
                                                              airtable_dict=request.get_json())
        record_response = airtable_object.update(record_id=record_id,
                                                 fields=update_json,
                                                 typecast=True)
        normalized_response = airtable_object.process_airtable_response(table=table,
                                                                        response=record_response)
        return jsonify(normalized_response)
    elif request.method == "DELETE":
        record_response = airtable_object.delete(record_id=record_id)
        return jsonify(record_response)

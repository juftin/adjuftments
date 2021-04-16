#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Endpoints for Accessing PostgreSQL Backend
"""

from datetime import datetime
import logging
from typing import List, Union

from dotenv import load_dotenv
from flask import abort, Blueprint, jsonify, request, Response
from flask_login import login_required
from sqlalchemy import func, Table

from adjuftments.application import db_session
from adjuftments.config import APIEndpoints, DOT_ENV_FILE_PATH
from adjuftments.schema import TABLE_FINDER

load_dotenv(DOT_ENV_FILE_PATH, override=True)
logger = logging.getLogger(__name__)

database = Blueprint(name="database", import_name=__name__)


@database.route(rule=f"{APIEndpoints.ADJUFTMENTS_BASE}/<table>", methods=["GET", "POST", "DELETE"])
@login_required
def interact_with_adjuftments_table(table: str) -> Response:
    """
    Interact with an Adjuftments SQL Table

    - GET requests will return all data (and additional filters can be passsed).
    - POST requests will create an Airtable record, given that the proper fields are passed as JSON

    Returns
    -------
    Response
    """
    adjuftments_table = TABLE_FINDER.get(table, None)
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
        response: List[Table] = adjuftments_table.query.filter_by(**request_args).limit(limit)
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
        db_session.merge(new_record)
        db_session.commit()
        logger.info(f"DB Record Inserted: {adjuftments_table.__tablename__} - {new_record.id}")
        return jsonify(new_record.to_dict())
    # INSERT DATA
    elif request.method == "DELETE":
        response = adjuftments_table.query.delete()
        db_session.commit()
        return jsonify(dict(truncated=True, table=table, timestamp=datetime.utcnow(),
                            rows=response))


@database.route(rule=f"{APIEndpoints.ADJUFTMENTS_BASE}/<table>/<key>",
                methods=["GET", "POST", "DELETE"])
@login_required
def interact_with_adjuftments_record(table: str, key: Union[str, int]) -> Response:
    """
    Retrieve a Single Record by its primary key

    Interact with an SAdjuftments SQL Table
    - GET requests will return all data (and additional filters can be passed).
    - POST requests will create an Airtable record, given that the proper fields are passed as JSON

    Returns
    -------
    Response
    """
    adjuftments_table = TABLE_FINDER.get(table, None)
    if adjuftments_table is None:
        abort(status=500,
              description=("Adjuftments table does not exist or "
                           f"is not externally accessible: {table}"))
    selected_row: Table = adjuftments_table.query.get(key)
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
            db_session.merge(updated_row)
            db_session.commit()
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
            db_session.delete(deleted_row)
            db_session.commit()
            logger.info(f"DELETE: Row Deleted: {table} - {key}")
            formatted_response = selected_row.to_dict()
            return jsonify(formatted_response)


@database.route(rule=f"{APIEndpoints.ADJUFTMENTS_BASE}/<table>/<date_column>/max",
                methods=["GET"])
@login_required
def get_max_date_from_table(table: str, date_column: str) -> Response:
    """
    Retrieve a Max Date Column from Table

    Parameters
    ----------
    table: str
        DB Table
    date_column: str
        column name

    Returns
    -------
    Response
    """
    database_table = TABLE_FINDER.get(table, None)
    if database_table is None:
        abort(status=500, description=f"Table doesn't exist: {table}")
    database_column = getattr(database_table, date_column)
    response = db_session.query(func.max(database_column)).first()
    if response[0] is None:
        max_value = None
    else:
        max_value = response[0]
    return jsonify({date_column: max_value})

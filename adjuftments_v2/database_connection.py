#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Database Interactions
"""

from datetime import datetime
from json import dumps, loads
import logging
from typing import List

from sqlalchemy import func

from adjuftments_v2.application import db
from adjuftments_v2.models import ExpensesTable, MODEL_FINDER
from adjuftments_v2.utils import AdjuftmentsEncoder

logger = logging.getLogger(__name__)


def query_table(table: str, query_filter: dict = None,
                query_order: dict = None, limit: bool = None) -> List[dict]:
    """
    Retrieve a single row from a database table

    Parameters
    ----------
    table: str
        Database table
    query_filter: dict
        Query filter as dict
    query_order: dict
        Dictionary to order query by
    limit: int
        Query Limit

    Returns
    -------
    List[dict]
    """
    database_table = MODEL_FINDER[table]
    if query_filter is None:
        query_filter = dict()
    if query_order is None:
        query_order = dict()
    database_response = database_table.query.filter_by(**query_filter).order_by(
        **query_order).limit(limit)
    compiled_response = list()
    for record in database_response:
        cleaned_response = dumps(record.to_dict(), cls=AdjuftmentsEncoder)
        compiled_response.append(loads(cleaned_response))
    return compiled_response


def return_single_row(table: str, query_filter: dict = None,
                      query_order: dict = None, key: str = None) -> dict:
    """
    Retrieve a single row from a database table

    Parameters
    ----------
    table: str
        Database table
    query_filter: dict
        Query filter as dict
    query_order: dict
        Dictionary to order query by
    key: str
        Single column's value to return

    Returns
    -------
    dict
    """
    database_table = MODEL_FINDER[table]
    if query_filter is None:
        query_filter = dict()
    if query_order is None:
        query_order = dict()
    response = database_table.query.filter_by(**query_filter).order_by(
        **query_order).first()
    cleaned_response = dumps(response.to_dict(), cls=AdjuftmentsEncoder)
    formatted_response = loads(cleaned_response)
    if key is not None:
        return formatted_response[key]
    else:
        return formatted_response


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
    database_table = MODEL_FINDER[table]
    database_column = getattr(database_table, date_column)
    response = db.session.query(func.max(database_column)).first()
    if replace_none is True and response[0] is None:
        response = (datetime(year=1975, month=1, day=1), None)
    max_value = response[0]
    return max_value


def get_last_expense() -> dict:
    """
    Retrieve the most recent expense from the database

    Returns
    -------
    dict
    """
    response = ExpensesTable.query.order_by(ExpensesTable.date.desc(),
                                            ExpensesTable.imported_at.desc()).first()
    cleaned_response = dumps(response.to_dict(), cls=AdjuftmentsEncoder)
    formatted_response = loads(cleaned_response)
    return formatted_response

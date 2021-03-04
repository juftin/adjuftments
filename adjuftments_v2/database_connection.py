#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Database Interactions
"""

from json import dumps, loads
from typing import List

from adjuftments_v2.models import ExpensesTable, MODEL_FINDER
from adjuftments_v2.utils import AdjuftmentsEncoder


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
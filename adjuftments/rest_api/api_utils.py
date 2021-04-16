#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
API Utilities for Auth / Database Connections - Functions Imported in __init__
"""

from ast import literal_eval
import logging
from os import getenv
from typing import Optional

from dotenv import load_dotenv
from flask import request

from adjuftments.application import app, db_session, login_manager
from adjuftments.config import APIDefaultConfig, DOT_ENV_FILE_PATH
from adjuftments.schema import UsersTable

load_dotenv(DOT_ENV_FILE_PATH, override=True)
logger = logging.getLogger(__name__)


# noinspection PyUnusedLocal
@app.teardown_appcontext
def shutdown_session(exception: Optional[object] = None) -> None:
    """
    This Is a Mandatory Function that assits with database Connections

    Parameters
    ----------
    exception: Optional[object]

    Returns
    -------

    """
    db_session.remove()


@login_manager.request_loader
def load_user_from_request(flask_request: request) -> Optional[UsersTable]:
    """
    Assert a Header's token Auth is in the users table. This is the function that
    manages API Auth

    Parameters
    ----------
    flask_request: request

    Returns
    -------
    Optional[UsersTable]
    """
    api_token = flask_request.headers.get("Authorization")
    disable_api_security = literal_eval(getenv("DISABLE_API_SECURITY", "False"))
    if api_token is not None and disable_api_security is False:
        api_token = api_token.replace('Bearer ', '', 1)
        user = UsersTable.query.filter_by(api_token=api_token).first()
        if user is not None:
            return user
    elif disable_api_security is True:
        user = UsersTable.query.filter_by(api_token=APIDefaultConfig.API_TOKEN).first()
        if user is not None:
            return user
    return None

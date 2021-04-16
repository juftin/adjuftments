#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Endpoints for API Administration
"""

from datetime import datetime
import logging

from dotenv import load_dotenv
from flask import abort, Blueprint, jsonify, request, Response
from flask_login import login_required
from sqlalchemy.sql.ddl import CreateSchema

from adjuftments.application import Base, db_session, engine
from adjuftments.config import APIDefaultConfig, APIEndpoints, DOT_ENV_FILE_PATH
from adjuftments.schema import UsersTable

load_dotenv(DOT_ENV_FILE_PATH, override=True)
logger = logging.getLogger(__name__)

admin = Blueprint(name="admin", import_name=__name__)


@admin.route(rule=APIEndpoints.ADMIN_DATABASE_BUILD, methods=["POST"])
def prepare_database() -> Response:
    """
    Build the Database Tables defined in the ALL_TABLES var
    """
    from adjuftments.schema import ALL_TABLES
    logger.info(f"Preparing Database: {len(ALL_TABLES)} table(s)")
    if not engine.dialect.has_schema(engine, "adjuftments"):
        engine.execute(CreateSchema("adjuftments"))
    request_json = request.get_json()
    drop_all = request_json.get("drop_all", False)
    if drop_all is True:
        Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    return jsonify(True)


@admin.route(rule=APIEndpoints.ADMIN_USERS, methods=["POST"])
def clean_start_system_users() -> Response:
    """
    Apart from the HEALTHCHECK, and ADMIN_DATABASE_BUILD This is the lone API Endpoint
    that doesn't require authentication, since it can only be called when the Admin Users
    Table is empty, (and no other endpoints will Auth until that table is populated)
    """
    error_description = ("The database isn't in a state for this "
                         f"endpoint to work: {APIEndpoints.ADMIN_USERS}")
    clean_start_param = request.json.get("clean_start")
    if clean_start_param is True:
        all_users = UsersTable.query.all()
        if len(all_users) != 0:
            abort(status=500, description=error_description)
        adjuftments_user = UsersTable(username=APIDefaultConfig.DATABASE_USERNAME)
        adjuftments_user.set_api_token(api_token=APIDefaultConfig.API_TOKEN)
        db_session.merge(adjuftments_user)
        db_session.commit()
        return jsonify(adjuftments_user.to_dict())
    else:
        abort(status=500, description=error_description)


@admin.route(rule=APIEndpoints.ADMIN_USERS, methods=["GET"])
@login_required
def interact_with_system_users() -> Response:
    """
    Get Data from the Users Table in the Database

    Returns
    -------
    Response
    """
    all_users = UsersTable.query.all()
    prepared_users = [user.to_dict() for user in all_users]
    return jsonify(prepared_users)


@admin.route(rule=APIEndpoints.HEALTHCHECK, methods=["GET"])
def check_api_health() -> Response:
    """
    Endpoint for checking health status of the API
    """
    return jsonify(dict(status=200, api_healthy=True,
                        updated_at=datetime.utcnow()))

#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Adjuftments REST API Module
"""
import logging
from typing import List

from flask import Blueprint

from adjuftments_v2.application import app
from .admin import admin
from .airtable import airtable
from .api_utils import load_user_from_request, shutdown_session
from .database_endpoints import database
from .finance_endpoints import finance
from .images_endpoints import images
from .splitwise_endpoints import splitwise

console_handler = logging.StreamHandler()
logging.basicConfig(format="%(asctime)s [%(levelname)8s]: %(message)s [%(name)s]",
                    handlers=[console_handler],
                    level=logging.INFO)

API_BLUEPRINTS: List[Blueprint] = [
    admin,
    airtable,
    database,
    finance,
    images,
    splitwise
]

for api_blueprint in API_BLUEPRINTS:
    app.register_blueprint(blueprint=api_blueprint)

__all__ = list()  # THIS DIRECTORY IS ONLY TO BE USED AS A WSGI ENGINE, NOT IMPORTED ELSEWHERE

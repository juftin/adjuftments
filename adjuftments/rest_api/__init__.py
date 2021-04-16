#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Adjuftments REST API Module
"""

import logging
from typing import List

from flask import Blueprint

from adjuftments.application import app
from .admin import admin
from .airtable import airtable
from .api_utils import load_user_from_request, shutdown_session
from .database import database
from .finance import finance
from .images import images
from .splitwise import splitwise

console_handler = logging.StreamHandler()
logging.basicConfig(format="%(asctime)s [%(levelname)8s]: %(message)s [%(name)s]",
                    handlers=[console_handler],
                    level=logging.WARNING)

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

__all__ = list()  # SET EVERYTHING TO PRIVATE

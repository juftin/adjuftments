# !/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Adjuftments Root __init__
"""

import logging

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from adjuftments_v2.config import flask_config

logger = logging.getLogger(__name__)
app = Flask(__name__)
app.config.from_object(flask_config.FlaskDefaultConfig)
db = SQLAlchemy(app=app)
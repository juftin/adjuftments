# !/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Adjuftments Root __init__
"""

from flask import Flask as _Flask
from flask_sqlalchemy import SQLAlchemy as _SQLAlchemy

from .airtable_connection import Airtable
from .config import flask_config as _flask_config
from .splitwise_connection import Splitwise

app = _Flask(__name__)
app.config.from_object(_flask_config.FlaskDefaultConfig)
db = _SQLAlchemy(app=app)

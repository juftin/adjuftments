# !/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Adjuftments Root __init__
"""

import logging

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

from adjuftments_v2.config import FlaskDefaultConfig
from adjuftments_v2.utils import AdjuftmentsEncoder

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(FlaskDefaultConfig)
app.json_encoder = AdjuftmentsEncoder

login_manager = LoginManager()
login_manager.init_app(app)

db = SQLAlchemy(app=app)

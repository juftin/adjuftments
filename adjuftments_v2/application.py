# !/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Adjuftments Root __init__
"""

import logging

from flask import Flask
from flask_login import LoginManager
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from adjuftments_v2.config import FlaskDefaultConfig
from adjuftments_v2.utils import AdjuftmentsEncoder

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(FlaskDefaultConfig)
app.json_encoder = AdjuftmentsEncoder

login_manager = LoginManager()
login_manager.init_app(app)

engine = create_engine(FlaskDefaultConfig.SQLALCHEMY_DATABASE_URI)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

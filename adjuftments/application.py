# !/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Adjuftments Root __init__
"""

import logging
from os.path import join
from pathlib import Path

from flask import Flask
from flask_login import LoginManager
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from adjuftments.config import APIDefaultConfig, DOT_ENV_FILE_PATH
from adjuftments.utils import AdjuftmentsEncoder

logger = logging.getLogger(__name__)

templates = join(Path(DOT_ENV_FILE_PATH).parent, "adjuftments",
                 "rest_api", "templates")
app = Flask(__name__, template_folder=templates)
app.config.from_object(APIDefaultConfig)
app.json_encoder = AdjuftmentsEncoder

login_manager = LoginManager()
login_manager.init_app(app)

engine = create_engine(APIDefaultConfig.SQLALCHEMY_DATABASE_URI)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()

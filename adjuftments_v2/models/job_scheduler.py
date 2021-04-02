#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from sqlalchemy import func

from adjuftments_v2.application import db
from .utils import ModelDictionaryGenerator


class JobSchedulerTable(db.Model, ModelDictionaryGenerator):
    """
    Core Dashboard Table
    """
    __tablename__ = "job_scheduler"
    __table_args__ = {"schema": "adjuftments"}

    id = db.Column(db.VARCHAR(191), primary_key=True, unique=True, nullable=False)
    next_run_time = db.Column(db.Numeric(precision=15), index=True)
    job_state = db.Column(db.LargeBinary())
    created_at = db.Column(db.DateTime(timezone="UTC"), nullable=False,
                           server_default=func.now(timezone="utc"))

    def __repr__(self):
        return f"<{self.__tablename__}: {self.measure}>"

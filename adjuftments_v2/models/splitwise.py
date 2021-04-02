#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from adjuftments_v2.application import db
from .utils import ModelDictionaryGenerator


class SplitwiseTable(db.Model, ModelDictionaryGenerator):
    """
    Core Splitwise Table
    """
    __tablename__ = "splitwise"
    __table_args__ = {"schema": "adjuftments"}

    id = db.Column(db.Integer(), primary_key=True, unique=True, nullable=False, index=True)
    date = db.Column(db.DateTime(timezone="UTC"), nullable=False)
    transaction_balance = db.Column(db.Numeric(10, 2), nullable=False)
    cost = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.String(512), nullable=False)
    category = db.Column(db.String(32), nullable=False)
    currency = db.Column(db.String(32), nullable=False)
    payment = db.Column(db.Boolean, nullable=False)
    deleted = db.Column(db.Boolean, nullable=False)
    created_by = db.Column(db.Integer(), nullable=False)
    created_at = db.Column(db.DateTime(timezone="UTC"), nullable=False)
    deleted_at = db.Column(db.DateTime(timezone="UTC"), nullable=True)
    updated_at = db.Column(db.DateTime(timezone="UTC"), nullable=False)

    def __repr__(self):
        return f"<{self.__tablename__}: {self.id}>"

#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from adjuftments_v2.application import db
from .utils import ModelDictionaryGenerator


class ExpensesTable(db.Model, ModelDictionaryGenerator):
    """
    Core Expenses Table
    """
    __tablename__ = "expenses"
    __table_args__ = {"schema": "adjuftments"}

    id = db.Column(db.String(32), primary_key=True, unique=True, nullable=False, index=True)
    date = db.Column(db.DateTime(timezone="UTC"), nullable=False)
    amount = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    transaction = db.Column(db.String(512), nullable=False)
    category = db.Column(db.String(32), nullable=False)
    imported = db.Column(db.Boolean, default=False, nullable=False)
    imported_at = db.Column(db.DateTime(timezone="UTC"), nullable=True)
    splitwise = db.Column(db.Boolean, default=False, nullable=False)
    delete = db.Column(db.Boolean, default=False, nullable=False)
    uuid = db.Column(db.String(128), nullable=True)
    splitwise_id = db.Column(db.Integer(), db.ForeignKey("adjuftments.splitwise.id"),
                             nullable=True)
    created_at = db.Column(db.DateTime(timezone="UTC"), nullable=False)
    updated_at = db.Column(db.DateTime(timezone="UTC"), nullable=False)

    def __repr__(self):
        return f"<{self.__tablename__}: {self.id}>"

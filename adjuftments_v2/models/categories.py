#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from sqlalchemy import func

from adjuftments_v2.application import db
from .utils import ModelDictionaryGenerator


class CategoriesTable(db.Model, ModelDictionaryGenerator):
    """
    Core Dashboard Table
    """
    __tablename__ = "categories"
    __table_args__ = {"schema": "adjuftments"}

    id = db.Column(db.String(32), primary_key=True, unique=True, nullable=False)
    category = db.Column(db.String(32), unique=True, nullable=False, index=True)
    amount_spent = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    percent_of_total = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    created_at = db.Column(db.DateTime(timezone="UTC"), nullable=False)
    updated_at = db.Column(db.DateTime(timezone="UTC"), nullable=False,
                           server_default=func.now(timezone="utc"),
                           onupdate=func.now(timezone="utc"))

    def __repr__(self):
        return f"<{self.__tablename__}: {self.category}>"

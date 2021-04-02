#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from sqlalchemy import func

from adjuftments_v2.application import db
from .utils import ModelDictionaryGenerator


class StocksTable(db.Model, ModelDictionaryGenerator):
    """
    Core Stocks Table
    """
    __tablename__ = "stocks"
    __table_args__ = {"schema": "adjuftments"}

    id = db.Column(db.String(32), primary_key=True, unique=True, nullable=False, index=True)
    ticker = db.Column(db.String(32), unique=False, nullable=False)
    stock_price = db.Column(db.Numeric(10, 2), nullable=True)
    value = db.Column(db.Numeric(10, 2), nullable=True)
    holdings = db.Column(db.Numeric(10, 3), nullable=True)
    description = db.Column(db.String(32), unique=True, nullable=False, index=True)
    cost_basis = db.Column(db.Numeric(10, 2), nullable=True)
    created_at = db.Column(db.DateTime(timezone="UTC"), nullable=False)
    updated_at = db.Column(db.DateTime(timezone="UTC"), nullable=False,
                           server_default=func.now(timezone="utc"),
                           onupdate=func.now(timezone="utc"))

    def __repr__(self):
        return f"<{self.__tablename__}: {self.ticker}>"

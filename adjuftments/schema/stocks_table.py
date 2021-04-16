#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from sqlalchemy import Column, DateTime, func, Numeric, String

from adjuftments.application import Base
from .utils import TableDictionaryGenerator


class StocksTable(Base, TableDictionaryGenerator):
    """
    Core Stocks Table
    """
    __tablename__ = "stocks"
    __table_args__ = {"schema": "adjuftments"}

    id = Column(String(32), primary_key=True, unique=True, nullable=False, index=True)
    ticker = Column(String(32), unique=False, nullable=False)
    stock_price = Column(Numeric(10, 2), nullable=True)
    value = Column(Numeric(10, 2), nullable=True)
    holdings = Column(Numeric(10, 3), nullable=True)
    description = Column(String(32), unique=True, nullable=False, index=True)
    cost_basis = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime(timezone="UTC"), nullable=False)
    updated_at = Column(DateTime(timezone="UTC"), nullable=False,
                        server_default=func.now(timezone="utc"),
                        onupdate=func.now(timezone="utc"))

    def __repr__(self):
        return f"<{self.__tablename__}: {self.ticker}>"

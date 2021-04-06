#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String

from adjuftments_v2.application import Base
from .utils import TableDictionaryGenerator


class ExpensesTable(Base, TableDictionaryGenerator):
    """
    Core Expenses Table
    """
    __tablename__ = "expenses"
    __table_args__ = {"schema": "adjuftments"}

    id = Column(String(32), primary_key=True, unique=True, nullable=False, index=True)
    date = Column(DateTime(timezone="UTC"), nullable=False)
    amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    transaction = Column(String(512), nullable=False)
    category = Column(String(32), nullable=False)
    imported = Column(Boolean, default=False, nullable=False)
    imported_at = Column(DateTime(timezone="UTC"), nullable=True)
    splitwise = Column(Boolean, default=False, nullable=False)
    delete = Column(Boolean, default=False, nullable=False)
    uuid = Column(String(128), nullable=True)
    splitwise_id = Column(Integer(), ForeignKey("adjuftments.splitwise.id"),
                          nullable=True)
    created_at = Column(DateTime(timezone="UTC"), nullable=False)
    updated_at = Column(DateTime(timezone="UTC"), nullable=False)

    def __repr__(self):
        return f"<{self.__tablename__}: {self.id}>"

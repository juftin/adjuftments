#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String

from adjuftments.application import Base
from .accounts_table import AccountsTable
from .splitwise_table import SplitwiseTable
from .utils import TableDictionaryGenerator


class ExpensesTable(Base, TableDictionaryGenerator):
    """
    Core EXPENSES Table
    """
    __tablename__ = "expenses"
    __table_args__ = {"schema": "adjuftments"}

    id = Column(String(32), primary_key=True, unique=True, nullable=False, index=True)
    date = Column(DateTime(timezone="UTC"), nullable=False)
    amount = Column(Numeric(10, 2), default=0.00, nullable=False)
    transaction = Column(String(512), nullable=False)
    category = Column(String(32), nullable=False)
    account = Column(String(32), ForeignKey(AccountsTable.id), nullable=True)
    account_name = Column(String(64), nullable=True)
    imported = Column(Boolean, default=False, nullable=False)
    imported_at = Column(DateTime(timezone="UTC"), nullable=True)
    splitwise = Column(Boolean, default=False, nullable=False)
    delete = Column(Boolean, default=False, nullable=False)
    uuid = Column(String(128), nullable=True)
    splitwise_id = Column(Integer(), ForeignKey(SplitwiseTable.id), nullable=True)
    created_at = Column(DateTime(timezone="UTC"), nullable=False)
    updated_at = Column(DateTime(timezone="UTC"), nullable=False)

    def __repr__(self):
        return f"<{self.__tablename__}: {self.id}>"

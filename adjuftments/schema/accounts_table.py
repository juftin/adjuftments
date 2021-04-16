#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from sqlalchemy import Boolean, Column, DateTime, func, Numeric, String

from adjuftments.application import Base
from .utils import TableDictionaryGenerator


class AccountsTable(Base, TableDictionaryGenerator):
    """
    Core Accounts Table to store bank account information
    """
    __tablename__ = "accounts"
    __table_args__ = {"schema": "adjuftments"}

    id = Column(String(32), primary_key=True, unique=True, nullable=False, index=True)
    name = Column(String(64), nullable=False)
    type = Column(String(64), nullable=False)
    description = Column(String(256), nullable=True)
    balance = Column(Numeric(10, 2), default=0.00, nullable=False)
    starting_balance = Column(Numeric(10, 2), default=0.00, nullable=False)
    default = Column(Boolean(), default=False, nullable=False)
    created_at = Column(DateTime(timezone="UTC"), nullable=False)
    updated_at = Column(DateTime(timezone="UTC"), nullable=False,
                        server_default=func.now(timezone="utc"),
                        onupdate=func.now(timezone="utc"))

    def __repr__(self):
        return f"<{self.__tablename__}: {self.name}>"

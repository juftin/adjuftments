#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String

from adjuftments_v2.application import Base
from .utils import ModelDictionaryGenerator


class SplitwiseTable(Base, ModelDictionaryGenerator):
    """
    Core Splitwise Table
    """
    __tablename__ = "splitwise"
    __table_args__ = {"schema": "adjuftments"}

    id = Column(Integer(), primary_key=True, unique=True, nullable=False, index=True)
    date = Column(DateTime(timezone="UTC"), nullable=False)
    transaction_balance = Column(Numeric(10, 2), nullable=False)
    cost = Column(Numeric(10, 2), nullable=False)
    description = Column(String(512), nullable=False)
    category = Column(String(32), nullable=False)
    currency = Column(String(32), nullable=False)
    payment = Column(Boolean, nullable=False)
    deleted = Column(Boolean, nullable=False)
    created_by = Column(Integer(), nullable=False)
    created_at = Column(DateTime(timezone="UTC"), nullable=False)
    deleted_at = Column(DateTime(timezone="UTC"), nullable=True)
    updated_at = Column(DateTime(timezone="UTC"), nullable=False)

    def __repr__(self):
        return f"<{self.__tablename__}: {self.id}>"

#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from sqlalchemy import Column, DateTime, func, Numeric, String

from adjuftments_v2.application import Base
from .utils import ModelDictionaryGenerator


class CategoriesTable(Base, ModelDictionaryGenerator):
    """
    Core Dashboard Table
    """
    __tablename__ = "categories"
    __table_args__ = {"schema": "adjuftments"}

    id = Column(String(32), primary_key=True, unique=True, nullable=False)
    category = Column(String(32), unique=True, nullable=False, index=True)
    amount_spent = Column(Numeric(10, 2), default=0.00, nullable=False)
    percent_of_total = Column(Numeric(10, 2), default=0.00, nullable=False)
    created_at = Column(DateTime(timezone="UTC"), nullable=False)
    updated_at = Column(DateTime(timezone="UTC"), nullable=False,
                        server_default=func.now(timezone="utc"),
                        onupdate=func.now(timezone="utc"))

    def __repr__(self):
        return f"<{self.__tablename__}: {self.category}>"

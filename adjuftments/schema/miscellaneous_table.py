#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from sqlalchemy import Column, DateTime, func, String

from adjuftments.application import Base
from .utils import TableDictionaryGenerator


class MiscellaneousTable(Base, TableDictionaryGenerator):
    """
    Core Miscellaneous Table
    """
    __tablename__ = "miscellaneous"
    __table_args__ = {"schema": "adjuftments"}

    id = Column(String(32), primary_key=True, unique=True, nullable=False)
    measure = Column(String(32), primary_key=True, unique=True, nullable=False, index=True)
    value = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone="UTC"), nullable=False)
    updated_at = Column(DateTime(timezone="UTC"), nullable=False,
                        server_default=func.now(timezone="utc"),
                        onupdate=func.now(timezone="utc"))

    def __repr__(self):
        return f"<{self.__tablename__}: {self.measure}>"

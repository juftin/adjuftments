#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from flask_login import UserMixin
from sqlalchemy import Column, DateTime, func, Integer, String

from adjuftments_v2.application import Base
from .utils import TableDictionaryGenerator


class UsersTable(UserMixin, Base, TableDictionaryGenerator):
    """
    Flask Login User Object
    """
    __tablename__ = "users"
    __table_args__ = {"schema": "adjuftments"}

    id = Column(Integer(), primary_key=True, unique=True, nullable=False, autoincrement=True)
    username = Column(String(64), unique=True, nullable=False)
    api_token = Column(String(128), nullable=True, index=True)
    created_at = Column(DateTime(timezone="UTC"), nullable=False,
                        server_default=func.now(timezone="utc"))
    updated_at = Column(DateTime(timezone="UTC"), nullable=False,
                        server_default=func.now(timezone="utc"),
                        onupdate=func.now(timezone="utc"))

    def set_api_token(self, api_token: str):
        """
        Create a hashed password/API token field

        Parameters
        ----------
        api_token: str

        Returns
        -------
        str
        """
        self.api_token = api_token
        return self.api_token

    def __repr__(self):
        return f"<{self.__tablename__}: {self.id}>"

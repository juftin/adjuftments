#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from airtable import Airtable as AirtablePythonWrapper

from adjuftments_v2.config import AirtableConfig


class Airtable(AirtablePythonWrapper):
    """
    Python Class for interacting with Airtable
    """
    __VERSION__ = 2.0

    def __init__(self, base: str, table: str, api_key: str = None) -> None:
        """
        Instantiation of Airtable Class. Requires Base, Table, and API Key

        Parameters
        ----------
        base: str
            Airtable Base Identifier
        table: str
            Airtable Table Name
        api_key: str
            Airtable API Key. Defaults to `AIRTABLE_API_KEY` environement variable
            if not supplied
        """
        self.base = base
        self.table = table
        if api_key is None:
            self.api_key = AirtableConfig.AIRTABLE_API_KEY
        elif api_key is not None:
            self.api_key = api_key
        super().__init__(base_key=self.base,
                         table_name=self.table,
                         api_key=self.api_key)

    def __repr__(self) -> str:
        """
        String Representation
        """
        return f"< Airtable: {self.table} >"

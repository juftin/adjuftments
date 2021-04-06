#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Adjuftments Model Extension Class
"""

from typing import Dict

from sqlalchemy import Column, Table


class TableDictionaryGenerator(object):
    """
    Basic Class to Convert Database Tables to Dictionaries. This class
    only has a single function that it extends onto Table classes: to_dict()
    """

    def to_dict(self: Table) -> Dict[str, Column]:
        """
        Return a flat dictionary with column mappings

        Returns
        -------
        Dict[str, object]
        """
        table_dictionary = dict()
        # noinspection PyUnresolvedReferences
        for column in self.__table__.columns:
            table_dictionary[column.name] = getattr(self, column.name)
        return table_dictionary

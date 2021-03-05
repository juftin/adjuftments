#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Generic Utilities for Adjuftments
"""

from datetime import date, timedelta
from datetime import datetime
import decimal
from json import dumps, loads

from flask.json import JSONEncoder


class AdjuftmentsEncoder(JSONEncoder):
    """
    App Wide JSON Encoder
    """

    def default(self, obj):
        """
        Default JSON Encoding
        """
        try:
            if isinstance(obj, date):
                return obj.isoformat()
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, decimal.Decimal):
                return float(obj)
            elif isinstance(obj, timedelta):
                return str(obj)
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)

    @staticmethod
    def parse_object(obj) -> object:
        """
        Parse and object

        Parameters
        ----------
        obj: obj

        Returns
        -------
        object
        """
        cleaned_response = dumps(obj, cls=AdjuftmentsEncoder)
        formatted_response = loads(cleaned_response)
        return formatted_response

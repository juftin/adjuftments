#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
JSON PArsing Utility for Adjuftments
"""

from datetime import date, datetime, timedelta
import decimal
from json import dumps, loads
import logging

from flask.json import JSONEncoder

logger = logging.getLogger(__name__)


class AdjuftmentsEncoder(JSONEncoder):
    """
    App Wide JSON Encoder + Additional Formatting Functions
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

    @staticmethod
    def format_float(amount: float, float_format: str = "money") -> str:
        """
        Format Floats to be pleasant and human readable

        Parameters
        ----------
        amount: float
            Float Amount to be converted into a string
        float_format: str
            Type of String to format into (accepts "money" and "percent")

        Returns
        -------
        str
        """
        # FORMAT MONEY FLOATS
        if float_format == "money":
            if amount < 0:
                float_string = "$ ({:,.2f})".format(
                    float(amount)).replace("-", "")
            elif amount >= 0:
                float_string = "$ {:,.2f}".format(
                    float(amount))
        # FORMAT PERCENTAGE FLOATS
        elif float_format == "percent":
            if amount < 0:
                float_string = "({:.4f}) %".format(
                    float(amount) * 100).replace("-", "")
            elif amount >= 0:
                float_string = "{:.4f} %".format(
                    float(amount) * 100)
        else:
            float_string = str(amount)
        return float_string

    @staticmethod
    def parse_adjuftments_description(description: str, default_string: str) -> str:
        """
        Prepare a Description for Splitwise

        Parameters
        ----------
        description: str
        default_string: str

        Returns
        -------
        str
        """
        parsed_description = description.split(" - ")
        if len(parsed_description) == 1:
            parsed_description = [default_string] + parsed_description
        parsed_description = [str(item).strip() for item in parsed_description]
        return " - ".join(parsed_description)

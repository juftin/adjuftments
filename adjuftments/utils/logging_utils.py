#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Logging / Notification Utility for Adjuftments
"""

import logging
from math import ceil
from os import environ
from typing import List, Optional

from dotenv import load_dotenv
from requests import post, Response

from adjuftments.config import DOT_ENV_FILE_PATH
from .parsing_utils import AdjuftmentsEncoder

load_dotenv(DOT_ENV_FILE_PATH, override=True)
logger = logging.getLogger(__name__)


class AdjuftmentsNotifications(logging.StreamHandler):
    """
    Push Notifications via Pushover - as a logging handler and helpful class
    """

    pushover_push_token: str = environ["PUSHOVER_PUSH_TOKEN"]
    pushover_push_user: str = environ["PUSHOVER_PUSH_USER"]

    def __init__(self, level: Optional[int] = logging.INFO):
        logging.StreamHandler.__init__(self)
        self.setLevel(level=level)

    def __repr__(self):
        return "<AdjuftmentsNotifications>"

    @staticmethod
    def send_message(message: str, **kwargs) -> Response:
        """
        Send a message via Pushover

        Parameters
        ----------
        message: str

        Returns
        -------
        Response
        """
        response = post(url="https://api.pushover.net/1/messages.json",
                        headers={"Content-Type": "application/json"},
                        params=dict(token=AdjuftmentsNotifications.pushover_push_token,
                                    user=AdjuftmentsNotifications.pushover_push_user,
                                    message=message,
                                    **kwargs)
                        )
        return response

    def emit(self, record):
        """
        Produce a logging record

        Parameters
        ----------
        record: str
            Message to log
        """
        log_formatted_message = "[{:>10}]: {}".format(record.levelname.upper(),
                                                      record.msg)
        title = f"Adjuftments {record.levelname.title()} Message"
        self.send_message(message=log_formatted_message, title=title)

    @staticmethod
    def log_splitwise_expenses(splitwise_data_array: List[dict]) -> None:
        """
        Log Splitwise Transactions to Pushover

        Parameters
        ----------
        splitwise_data_array: List[dict]

        Returns
        -------
        None
        """
        logging_array = AdjuftmentsNotifications._generate_splitwise_logging_array(
            splitwise_data_array=splitwise_data_array)
        for logging_record in logging_array:
            transaction_type = logging_record["type"]
            splitwise_transaction = logging_record["record"]
            transaction_cost = AdjuftmentsEncoder.format_float(amount=splitwise_transaction['cost'],
                                                               float_format='money')
            transaction_balance = AdjuftmentsEncoder.format_float(
                amount=splitwise_transaction['transaction_balance'],
                float_format='money')

            description = f"<b>Description:</b> {splitwise_transaction['description']}"
            cost = f"<b>Cost:</b> {transaction_cost}"
            amount_owed = f"<b>Amount Owed:</b> {transaction_balance}"
            date = f"<b>Date:</b> {splitwise_transaction['date'][:10]}"
            status_dict = dict(NEW="New", UPDATE="Updated", DELETED="Deleted",
                               PAYMENT="New")
            if transaction_type == "PAYMENT":
                message_title = f"{status_dict[transaction_type]} Splitwise Payment"
                message_body = "\n".join([description, cost, date])
                sound = "cashregister"
            else:
                message_title = f"{status_dict[transaction_type]} Splitwise Expense"
                message_body = "\n".join([description, cost, amount_owed, date])
                sound = "vibrate"
            AdjuftmentsNotifications.send_message(message=message_body, title=message_title,
                                                  priority=0, sound=sound,
                                                  html=1)

    @staticmethod
    def log_airtable_expenses(airtable_data_array: List[dict]) -> None:
        """
        Log Splitwise Transactions to Pushover

        Parameters
        ----------
        airtable_data_array: List[dict]
            Array of airtable expenses

        Returns
        -------
        None
        """
        logging_array = AdjuftmentsNotifications._generate_airtable_logging_array(
            airtable_data_array=airtable_data_array)
        for logging_record in logging_array:
            transaction_type = logging_record["type"]
            airtable_transaction = logging_record["record"]
            transaction_amount = AdjuftmentsEncoder.format_float(
                amount=airtable_transaction['amount'],
                float_format='money')
            date = f"<b>Date:</b> {airtable_transaction['date'][:10]}"
            description = f"<b>Transaction:</b> {airtable_transaction['transaction']}"
            amount = f"<b>Amount:</b> {transaction_amount}"
            category = f"<b>Category:</b> {airtable_transaction['category']}"
            account = f"<b>Account:</b> {airtable_transaction['account_name']}"
            status_dict = dict(NEW="New", UPDATE="Updated", DELETED="Deleted")
            message_title = f"{status_dict[transaction_type]} Adjuftments Expense"
            message_body = "\n".join([description, amount, category, date, account])
            AdjuftmentsNotifications.send_message(message=message_body, title=message_title,
                                                  priority=0, sound="vibrate",
                                                  html=1)

    @classmethod
    def _generate_splitwise_logging_array(cls, splitwise_data_array: List[dict]) -> List[str]:
        """
        Given new Splitwise data to ingest, properly log it :)

        Parameters
        ----------
        splitwise_data_array: List[dict]
            Array of splitwise expenses

        Returns
        -------
        List[str]
        """
        if splitwise_data_array is None:
            return list()
        else:
            logging_array = list()
            for new_splitwise_record in splitwise_data_array:
                if new_splitwise_record["deleted"] is True:
                    logging_array.append(dict(type="DELETED", record=new_splitwise_record))
                elif new_splitwise_record["payment"] is True:
                    logging_array.append(dict(type="PAYMENT", record=new_splitwise_record))
                elif new_splitwise_record["updated_at"] == new_splitwise_record["created_at"]:
                    logging_array.append(dict(type="NEW", record=new_splitwise_record))
                elif new_splitwise_record["updated_at"] > new_splitwise_record["created_at"]:
                    logging_array.append(dict(type="UPDATE", record=new_splitwise_record))
            return logging_array

    @classmethod
    def _generate_airtable_logging_array(cls, airtable_data_array: List[dict]) -> List[str]:
        """
        Given new Airtable data to ingest, properly log it :)

        Parameters
        ----------
        airtable_data_array: List[dict]
            Array of airtable expenses

        Returns
        -------
        List[str]
        """
        if airtable_data_array is None:
            return list()
        else:
            logging_array = list()
            for new_airtable_record in airtable_data_array:
                if new_airtable_record["delete"] is True:
                    logging_array.append(dict(type="DELETED", record=new_airtable_record))
                elif new_airtable_record["imported_at"] is None:
                    logging_array.append(dict(type="NEW", record=new_airtable_record))
                elif new_airtable_record["imported_at"] is not None:
                    logging_array.append(dict(type="UPDATE", record=new_airtable_record))
                else:
                    raise NotImplementedError(str(new_airtable_record))
            return logging_array

    @staticmethod
    def notify(self: logging.Logger, message: str, *args, **kwargs) -> None:
        """
        Custom Logging Notification Level for Pushover Logging
        between logging.ERROR and logging.CRITICAL (45)

        Parameters
        ----------
        self: logging.Logger
        message: str
            Message String
        args
        kwargs

        Returns
        -------
        None
        """
        logging_difference = (logging.CRITICAL - logging.ERROR) / 2
        notification_level = logging.CRITICAL - ceil(logging_difference)
        logging.addLevelName(level=notification_level, levelName="NOTIFY")
        if self.isEnabledFor(level=notification_level):
            self._log(level=notification_level, msg=message, args=args, **kwargs)

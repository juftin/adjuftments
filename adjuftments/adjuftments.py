#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Adjuftments SDK
"""

from datetime import datetime, timedelta
from hashlib import sha256
from json import loads
from json.decoder import JSONDecodeError
import logging
from os import getenv
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import urljoin, urlunparse

from pytz import timezone
from requests import delete, get, post, Response

from adjuftments.config import AirtableConfig, APIEndpoints
from adjuftments.utils import AdjuftmentsEncoder, AdjuftmentsError, AdjuftmentsNotifications

logging.Logger.notify = AdjuftmentsNotifications.notify
logger = logging.getLogger(__name__)


class Adjuftments(object):
    """
    Python Wrapper Around the Adjuftments REST API.

    Examples
    ----------
    >>> from adjuftments import Adjuftments
    >>> from adjuftments.config import APIDefaultConfig
    >>>
    >>> adjuftments_engine = Adjuftments(endpoint=APIDefaultConfig.API_ENDPOINT,
    >>>                                  api_token=APIDefaultConfig.API_TOKEN,
    >>>                                  https=False, port=5000)
    """

    def __init__(self, endpoint: str, api_token: str,
                 port: int = 5000, https: bool = False):
        """
        Store the API Token, Port, and whether the connection uses HTTPS

        Parameters
        ----------
        endpoint: str
            REST API Endpoint
        api_token: str
            Adjuftments API Token
        port: int
            Adjuftments REST API Port, defaults to 500
        https: bool
            Whether the endpoint is behind HTTPS
        """
        self.scheme = "http" if https is False else "https"
        self.net_loc = endpoint if port is None else f"{endpoint}:{port}"

        self.port = port
        url_components = (self.scheme, self.net_loc, "", "", "", "")
        self.endpoint = urlunparse(components=url_components)
        self.headers = dict(Authorization=f"Bearer {api_token}")

    def __repr__(self) -> str:
        """
        String Representation of SDK
        """
        return f"<Adjuftments: {self.endpoint}>"

    def prepare_database(self, clean_start: Optional[Union[bool, str]] = "auto") -> None:
        """
        Generate the Initial Database

        Parameters
        ----------
        clean_start : Optional[Union[bool, str]]
            Whether to clean start the database by ingesting/replacing all data.
            Defaults to "auto"

        Returns
        -------
        None
        """
        if clean_start is True:
            logger.info("Initiating Clean Database Refresh")
            self._build_database(drop_all=True)
            self._clean_start(run=True)
        elif str(clean_start).lower() == "auto":
            logger.info("Initializing Database")
            try:
                data_size = len(self._get_db_data_soft_fail(table="expenses", params=dict(limit=1)))
                if data_size == 0:
                    logger.info("No pre-existing data found, initiating clean start")
                    self._build_database(drop_all=True)
                    self._clean_start(run=True)
                else:
                    logger.info("Pre-existing data found, skipping clean start")
                    self._build_database(drop_all=False)
            except JSONDecodeError:
                logger.info("Database is uninitialized, initiating clean start")
                self._build_database(drop_all=True)
                self._clean_start(run=True)
        else:
            self._build_database(drop_all=False)

    ######################################
    # DATA REFRESH FUNCTIONS - PUBLIC API
    ######################################

    def refresh_dashboard(self, updated_data: bool = False,
                          splitwise_balance: float = None) -> None:
        """
        Refresh the Adjuftments Dashboard

        Parameters
        ----------
        updated_data: bool
            Whether or not new data is available
        splitwise_balance : float
            Splitwise Balance to Update the Dashboard with

        Returns
        -------
        None
        """
        api_endpoint = urljoin(self.endpoint, APIEndpoints.DASHBOARD_GENERATOR)
        response = post(url=api_endpoint,
                        json=dict(splitwise_balance=splitwise_balance,
                                  updated_data=updated_data),
                        headers=self.headers)
        if response.status_code != 200:
            raise AdjuftmentsError(response.text)
        response_content = loads(response.content)["manifest"]
        for updated_record in response_content:
            logger.info(f"Updated Dashboard: {updated_record['measure']} - "
                        f"{updated_record['value']}")
        return response_content

    def refresh_adjuftments_data(self) -> Tuple[bool, Optional[float]]:
        """
        Refresh the Splitwise / Airtable Data, Return an updated
        Splitwise balance if new updates exist

        Returns
        -------
        Tuple[bool, Optional[float]]
        """
        updated_splitwise_balance = self.refresh_splitwise_data()
        airtable_changes = self.refresh_airtable_expenses_data()
        if updated_splitwise_balance is not None or airtable_changes > 0:
            updated_data = True
            self.refresh_categories_data()
        else:
            updated_data = False
        return updated_data, updated_splitwise_balance

    def refresh_splitwise_data(self) -> Optional[float]:
        """
        Refresh the Splitwise table with the most recent data. Return an updated balance if
        new updates exist

        Returns
        -------
        Optional[float]
        """

        recent_data = self._get_latest_splitwise_data()
        logger.info(f"Data Ingestion: Splitwise: {len(recent_data)} records")
        if len(recent_data) > 0:
            AdjuftmentsNotifications.log_splitwise_expenses(splitwise_data_array=recent_data)
            self._load_db_data(table="splitwise", data_array=recent_data)
            splitwise_balance = self._get_splitwise_balance()
        else:
            splitwise_balance = None

        success_manifest, delete_manifest = self._generate_splitwise_manifest(
            data_array=recent_data)
        for airtable_record in success_manifest:
            preexisting_data = self._get_db_data(
                table="expenses",
                params=dict(splitwise_id=airtable_record["splitwise_id"]))
            if preexisting_data:
                for preexisting_record in preexisting_data:
                    airtable_record["id"] = preexisting_record["id"]
                    self._upsert_airtable_expense(airtable_expense=airtable_record)
            else:
                new_airtable_expense = self._create_airtable_data(table="expenses",
                                                                  record=airtable_record)
                self._upsert_airtable_expense(airtable_expense=new_airtable_expense)
        for airtable_record_deletion in delete_manifest:
            logger.info(f"Setting Splitwise record to deleted: {airtable_record_deletion['id']}")
            preexisting_airtable_data = self._get_db_data(
                table="expenses",
                params=dict(splitwise_id=airtable_record_deletion["id"]))
            if len(preexisting_airtable_data) > 0:
                assert len(preexisting_airtable_data) == 1
                preexisting_airtable_record = preexisting_airtable_data[0]
                self._delete_airtable_data(table="expenses",
                                           record_id=preexisting_airtable_record["id"])
                self._delete_db_record(table="expenses",
                                       record_id=preexisting_airtable_record["id"])
            self._load_db_data(table="splitwise",
                               data_array=airtable_record_deletion)
        return splitwise_balance

    def refresh_airtable_expenses_data(self) -> int:
        """
        Refresh the Airtable data with the most recent data. Returns the number
        of new records for update

        Returns
        -------
        int
        """
        latest_airtable_data = self._get_new_airtable_expenses_data()
        logger.info(f"Data Ingestion: Airtable: {len(latest_airtable_data)} records")
        # LOOP THROUGH NEW DATA
        for index, airtable_expense in enumerate(latest_airtable_data):
            # IF THE RECORD CONTAINS DELETE
            if airtable_expense["delete"] is True:
                self._handle_airtable_delete_request(airtable_expense=airtable_expense)
            elif airtable_expense["splitwise"] is True:
                self._handle_airtable_splitwise_request(airtable_expense=airtable_expense)
            elif airtable_expense["splitwise_id"] is not None:
                existing_splitwise_expense = self._get_db_record(table="splitwise",
                                                                 record_id=airtable_expense[
                                                                     "splitwise_id"])
                if existing_splitwise_expense is None:
                    logger.warning("No matching splitwise expense found: "
                                   f"{airtable_expense['splitwise_id']}. "
                                   "Overriding with NULL")
                    airtable_expense["splitwise_id"] = None
                updated_expense = self._upsert_airtable_expense(airtable_expense=airtable_expense)
                latest_airtable_data[index] = updated_expense
                latest_airtable_data[index]["id"] = airtable_expense["id"]
            else:
                updated_expense = self._upsert_airtable_expense(airtable_expense=airtable_expense)
                latest_airtable_data[index] = updated_expense
                latest_airtable_data[index]["id"] = airtable_expense["id"]
        AdjuftmentsNotifications.log_airtable_expenses(airtable_data_array=latest_airtable_data)
        return len(latest_airtable_data)

    def refresh_stocks_data(self) -> None:
        """
        Refresh the Airtable data with the most recent data

        Returns
        -------
        None
        """
        stocks_data = self._get_db_data(table="stocks")
        for stocks_record in stocks_data:
            ticker = stocks_record["ticker"]
            historical_price = stocks_record["stock_price"]
            stock_object = self._get_stock_ticker(ticker=ticker)
            new_price = stock_object["price"]
            if historical_price != new_price:
                formatted_price = AdjuftmentsEncoder.format_float(amount=new_price,
                                                                  float_format="money")
                formatted_message = f"Updating {ticker.upper()} price: {formatted_price}"
                logger.info(formatted_message)
            self._update_airtable_record(table="stocks", record_id=stocks_record["id"],
                                         fields={"Stock Price": stock_object["price"]})
        updated_stocks_data = self._get_airtable_data(table="stocks", params=None)
        self._load_db_data(table="stocks", data_array=updated_stocks_data)

    def refresh_categories_data(self) -> None:
        """
        Refresh the Airtable data with the most recent data

        Returns
        -------
        None
        """
        category_db_data = self._get_db_data(table="categories")
        updated_category_data = self._get_current_months_categories()
        db_categories = list()
        for db_record in category_db_data:
            category = db_record["category"]
            db_categories.append(category)
            original_amount = db_record.get("amount_spent", 0)
            try:
                new_amount = updated_category_data[category]["amount"]
            except KeyError:
                new_amount = 0
            if original_amount != new_amount:
                try:
                    percent_of_total = updated_category_data[category]["percent_of_total"] * 100
                except KeyError:
                    percent_of_total = 0
                new_db_record = db_record.copy()
                new_db_record["amount_spent"] = new_amount
                new_db_record["percent_of_total"] = percent_of_total
                self._load_db_record(table="categories", record=new_db_record)
                self._update_airtable_record(table="categories",
                                             record_id=new_db_record["id"],
                                             fields={"Amount Spent": new_amount,
                                                     "% of Total": percent_of_total})
        missing_categories = set(updated_category_data.keys()) - set(db_categories)
        for missing_category in missing_categories:
            new_airtable_record = self._create_airtable_data(
                table="categories",
                record={"Category": missing_category,
                        "Amount Spent": updated_category_data[missing_category]["amount"],
                        "% of Total": updated_category_data[missing_category]["percent_of_total"]})
            self._load_db_record(table="categories", record=new_airtable_record)

    ######################################
    # DATA RETRIEVAL FUNCTIONS
    ######################################

    def _get_airtable_data(self, table: str, params: Optional[dict] = None) -> dict:
        """
        Update a record in Airtable

        Parameters
        ----------
        table: str
            Airtable Table Name
        params: Optional[dict]
            Optional Parameters to pass to the request

        Returns
        -------
        dict
        """
        api_endpoint = urljoin(self.endpoint, f"{APIEndpoints.AIRTABLE_BASE}/{table}")
        response = get(url=api_endpoint, params=params, headers=self.headers)
        if response.status_code != 200:
            raise AdjuftmentsError(response.text)
        response_content = loads(response.content)
        return response_content

    def _get_new_airtable_expenses_data(self) -> List[dict]:
        """
        Get the latest data from splitwise

        Returns
        -------
        splitwise_data: List[dict]
        """
        new_data_filter = dict(formula="OR({Imported}=False(), {Delete}=True())")
        data_array = self._get_airtable_data(table="expenses", params=new_data_filter)
        return data_array

    def _get_splitwise_balance(self) -> float:
        """
        Get Splitwise Balance

        Returns
        -------
        float
        """
        api_endpoint = urljoin(self.endpoint, APIEndpoints.SPLITWISE_BALANCE)
        splitwise_response = get(url=api_endpoint, headers=self.headers)
        if splitwise_response.status_code != 200:
            logger.error(splitwise_response.text)
            raise AdjuftmentsError(splitwise_response.text)
        return loads(splitwise_response.content)["balance"]

    def _get_splitwise_data(self, params: Optional[dict] = None) -> dict:
        """
        Get and Process some Splitwise Data

        Parameters
        ----------
        params : Optional[dict]
            Optional Parameters to pass to the request

        Returns
        -------
        dict
        """
        api_endpoint = urljoin(self.endpoint, APIEndpoints.SPLITWISE_EXPENSES)
        splitwise_response = get(url=api_endpoint, params=params, headers=self.headers)
        if splitwise_response.status_code != 200:
            logger.error(splitwise_response.text)
            raise AdjuftmentsError(splitwise_response.text)
        return loads(splitwise_response.content)

    def _get_db_record(self, table: str, record_id: str) -> Optional[dict]:
        """
        Get a Database Record if it exists

        Parameters
        ----------
        table: str
            Database Table
        record_id: str
            Record ID

        Returns
        -------
        Optional[dict]
        """
        api_endpoint = urljoin(self.endpoint,
                               f"{APIEndpoints.ADJUFTMENTS_BASE}/{table}/{record_id}")
        splitwise_response = get(url=api_endpoint, headers=self.headers)
        if splitwise_response.status_code == 200:
            return loads(splitwise_response.content)
        else:
            return None

    def _get_db_data(self, table: str, params: dict = None) -> List[dict]:
        """
        Get data from a Database table

        Parameters
        ----------
        table: str
            Database Table
        params : Optional[dict]
            Optional Parameters to pass to the request

        Returns
        -------
        List[dict]
        """
        api_endpoint = urljoin(self.endpoint, f"{APIEndpoints.ADJUFTMENTS_BASE}/{table}")
        response = get(url=api_endpoint, params=params, headers=self.headers)
        if response.status_code != 200:
            raise AdjuftmentsError(response.text)
        return loads(response.content)

    def _get_db_data_soft_fail(self, table: str, params: dict = None) -> List[dict]:
        """
        Get data from a Database table, but don't raise an error if something goes wrong

        Parameters
        ----------
        table: str
            Database Table
        params : Optional[dict]
            Optional Parameters to pass to the request

        Returns
        -------
        List[dict]
        """
        api_endpoint = urljoin(self.endpoint, f"{APIEndpoints.ADJUFTMENTS_BASE}/{table}")
        response = get(url=api_endpoint, params=params, headers=self.headers)
        return loads(response.content)

    def _get_current_months_categories(self) -> List[dict]:
        """
        Get the current months expenses rolled up into categories

        Returns
        -------
        List[dict]
        """
        api_endpoint = urljoin(self.endpoint, APIEndpoints.EXPENSE_CATEGORIES)
        response = get(url=api_endpoint, headers=self.headers)
        if response.status_code != 200:
            raise AdjuftmentsError(response.text)
        return loads(response.content)

    def _get_max_timestamp(self, table: str, column: str) -> Dict[str, datetime]:
        """
        Get the latest modified timestamp from splitwise database table

        Parameters
        ----------
        table: str
            Database table name
        column: str
            Database column name

        Returns
        -------
        Dict[str, datetime]
        """
        api_endpoint = urljoin(self.endpoint,
                               f"{APIEndpoints.ADJUFTMENTS_BASE}/{table}/{column}/max")
        response = get(url=api_endpoint,
                       headers=self.headers)
        if response.status_code != 200:
            raise AdjuftmentsError(response.text)
        return loads(response.content)

    def _get_latest_splitwise_data(self) -> List[dict]:
        """
        Get the latest data from splitwise

        Returns
        -------
        recent_data: List[dict]
        """
        timestamp_column = "updated_at"
        max_splitwise_timestamp = self._get_max_timestamp(table="splitwise",
                                                          column=timestamp_column)
        timestamp_value = datetime.fromisoformat(max_splitwise_timestamp[timestamp_column])
        new_records_min = timestamp_value + timedelta(microseconds=1)

        params = dict(updated_after=new_records_min)
        recent_data = self._get_splitwise_data(params=params)
        return recent_data

    def _get_stock_ticker(self, ticker: str) -> dict:
        """
        Get the Stock Price object for a ticker

        Parameters
        ----------
        ticker: str
            Stock ticker

        Returns
        -------
        dict
        """
        api_endpoint = urljoin(self.endpoint, f"{APIEndpoints.STOCK_TICKER_API}/{ticker.lower()}")
        response = get(url=api_endpoint,
                       headers=self.headers)
        if response.status_code != 200:
            raise AdjuftmentsError(response.text)
        return loads(response.content)

    @classmethod
    def _get_miscellaneous_dict(cls, miscellaneous_data: List[dict]) -> dict:
        """
        Get the Miscellaneous Data as a Dictionary

        Parameters
        ----------
        miscellaneous_data : List[dict]

        Returns
        -------
        dict
        """
        miscellaneous_dict = dict()
        for miscellaneous_record in miscellaneous_data:
            miscellaneous_dict[miscellaneous_record["measure"]] = miscellaneous_record["value"]
        return miscellaneous_dict

    ######################################
    # DATA LOADING FUNCTIONS
    ######################################

    def _load_db_record(self, table: str, record: dict) -> dict:
        """
        Load record to database

        Parameters
        ----------
        table: str
            Database table name
        record: dict
            Record to load as dict

        Returns
        -------
        Response
        """
        api_endpoint = urljoin(self.endpoint, f"{APIEndpoints.ADJUFTMENTS_BASE}/{table}")
        response = post(url=api_endpoint, json=record, headers=self.headers)
        if response.status_code != 200:
            raise AdjuftmentsError(response.text)
        response_content = loads(response.content)
        logger.info(f"Upserted new {table} DB Record: {response_content['id']}")
        return loads(response.content)

    def _load_db_data(self, table: str, data_array: List[dict]) -> None:
        """
        Load data array to airtable

        Parameters
        ----------
        table: str
            Database table name
        data_array: List[dict]
            Array of records to load to the database

        Returns
        -------
        None
        """
        if isinstance(data_array, dict):
            data_array = [data_array]
        for expense_record in data_array:
            self._load_db_record(table=table, record=expense_record)

    ######################################
    # DATA UPDATING FUNCTIONS
    ######################################

    def _update_airtable_record(self, table: str, record_id: str, fields: dict,
                                params=None) -> dict:
        """
        Update a record in Airtable

        Parameters
        ----------
        table: str
            Database table name
        record_id: str
            Database record id
        fields: dict
            Dict to update table with

        Returns
        -------
        dict
        """
        api_endpoint = urljoin(self.endpoint, f"{APIEndpoints.AIRTABLE_BASE}/{table}/{record_id}")
        response = post(url=api_endpoint, json=fields, headers=self.headers, params=params)
        if response.status_code != 200:
            raise AdjuftmentsError(response.text)
        return loads(response.content)

    def _create_airtable_data(self, table: str, record: dict = None) -> dict:
        """
        Create a record in Airtable

        Parameters
        ----------
        table: str
            Database table name
        record: dict
            Airtable records as dict

        Returns
        -------
        dict
        """
        api_endpoint = urljoin(self.endpoint, f"{APIEndpoints.AIRTABLE_BASE}/{table}")
        response = post(url=api_endpoint, json=record, headers=self.headers)
        if response.status_code != 200:
            raise AdjuftmentsError(response.text)
        return loads(response.content)

    def _create_splitwise_data(self, record: dict) -> dict:
        """
        Create an expense in Splitwise. Requires "cost" and "description"
        fields to be passed in record

        Parameters
        ----------
        record: dict
            Splitwise record as dict

        Returns
        -------
        Response
        """
        api_endpoint = urljoin(self.endpoint, APIEndpoints.SPLITWISE_EXPENSES)
        response = post(url=api_endpoint, json=record, headers=self.headers)
        if response.status_code != 200:
            raise AdjuftmentsError(response.text)
        return loads(response.content)

    @staticmethod
    def create_imgur_image(image_data: bytes) -> dict:
        """
        Create an image in Imgur

        Parameters
        ----------
        image_data: bytes
            Image as binary data

        Returns
        -------
        dict
        """
        imgur_api_url = "https://api.imgur.com/3/image"
        headers = dict(Authorization=f"Client-ID {getenv('IMGUR_CLIENT_ID')}")
        response = post(url=imgur_api_url,
                        headers=headers,
                        data=image_data,
                        files=list())
        if response.status_code != 200:
            raise AdjuftmentsError(response.text)
        return loads(response.content)

    def _upsert_airtable_expense(self, airtable_expense: dict):
        """
        Upsert a record into Airtable as well as the database

        Parameters
        ----------
        airtable_expense: dict
            Expense as dict

        Returns
        -------
        updated_record: dict
            Provided expense, with any updates
        """
        record_id = airtable_expense["id"]
        if airtable_expense["splitwise"] is True:
            logger.error(f"This record shouldn't have Splitwise enabled {airtable_expense}")
            raise SystemError(f"This record shouldn't have Splitwise enabled {airtable_expense}")
        # UPSERT RECORD INTO DATABASE
        updated_record = self._prepare_expenses_record_for_upsert(record=airtable_expense)
        updated_record = AdjuftmentsEncoder.parse_object(obj=updated_record)
        self._load_db_record(table="expenses", record=updated_record)
        updated_record.pop("created_at", None)
        updated_record.pop("id")
        if not isinstance(updated_record["account"], list):
            updated_record["account"] = [updated_record["account"]]
        self._update_airtable_record(table="expenses", record_id=record_id,
                                     fields=updated_record)
        return updated_record

    def _prepare_expenses_record_for_upsert(self, record: dict) -> dict:
        """
        Set Important Fields on an expense record

        Parameters
        ----------
        record: dict
            Expense as dict

        Returns
        -------
        dict
        """
        updated_record = record.copy()
        updated_record["imported"] = True
        updated_record["imported_at"] = datetime.utcnow()
        updated_record["splitwise"] = False
        concatted_fields = (updated_record["transaction"] + str(updated_record["amount"]) +
                            updated_record["date"] + updated_record["category"])
        updated_record["uuid"] = sha256(concatted_fields.encode('utf-8')).hexdigest()
        expense_type = AdjuftmentsEncoder.categorize_expenses(
            transaction=updated_record["transaction"],
            category=updated_record["category"])
        primary_checking_record = self._get_db_data(
            table="accounts",
            params=dict(type="Checking"))[0]
        improper_savings = all([updated_record["account"] == primary_checking_record["id"],
                                expense_type == "Savings"])
        improper_checking = all([expense_type not in ["Savings", "Adjustment"],
                                 updated_record["category"] != "Interest",
                                 updated_record["account"] is not None,
                                 updated_record["account"] != primary_checking_record["id"]])
        if improper_savings is True:
            primary_savings_record = self._get_db_data(table="accounts",
                                                       params=dict(default=True, type="Savings"))[0]
            updated_record["account"] = primary_savings_record["id"]
            updated_record["account_name"] = primary_savings_record["name"]
            logger.notify("Improper Savings Account Configuration Identified. Setting to default "
                          f"savings account: {updated_record['id']}: "
                          f"{updated_record['transaction']}")
        elif improper_checking is True:
            updated_record["account"] = primary_checking_record["id"]
            updated_record["account_name"] = primary_checking_record["name"]
            logger.notify("Improper Checking Account Configuration Identified. Setting to default "
                          f"checking account: {updated_record['id']}: "
                          f"{updated_record['transaction']}")
        elif updated_record["account"] is None:
            updated_record["account"] = primary_checking_record["id"]
            updated_record["account_name"] = primary_checking_record["name"]
        return updated_record

    ######################################
    # DATA DELETION FUNCTIONS
    ######################################

    def _delete_airtable_data(self, table: str, record_id: str) -> Optional[dict]:
        """
        Delete a record from airtable

        Parameters
        ----------
        table: str
            Airtable Table
        record_id: str
            Airtable Record ID

        Returns
        -------
        Optional[dict]
        """
        api_endpoint = urljoin(self.endpoint, f"{APIEndpoints.AIRTABLE_BASE}/{table}/{record_id}")
        response = delete(url=api_endpoint, headers=self.headers)
        if response.status_code == 200:
            logger.info(f"Airtable Record Deleted: {table.title()} - {record_id}")
            return loads(response.content)
        else:
            return None

    def _delete_splitwise_data(self, record_id: str) -> Optional[dict]:
        """
        Delete a record from Splitwise

        Parameters
        ----------
        record_id: str
            Splitwise record ID

        Returns
        -------
        Optional[dict]
        """
        api_endpoint = urljoin(self.endpoint, f"{APIEndpoints.SPLITWISE_EXPENSES}/{record_id}")
        response = delete(url=api_endpoint, headers=self.headers)
        if response.status_code == 200:
            logger.info(f"Splitwise Record Deleted: {record_id}")
            return loads(response.content)
        else:
            return None

    def _delete_db_record(self, table: str, record_id: str) -> Optional[dict]:
        """
        Delete a record from the database

        Parameters
        ----------
        table: str
            Database Table
        record_id: str
            Database Record ID

        Returns
        -------
        Optional[dict]
        """
        api_endpoint = urljoin(self.endpoint,
                               f"{APIEndpoints.ADJUFTMENTS_BASE}/{table}/{record_id}")
        response = delete(url=api_endpoint, headers=self.headers)
        if response.status_code == 200:
            logger.info(f"Database Record Deleted: {table.title()} - {record_id}")
            return loads(response.content)
        else:
            return None

    def _truncate_db_table(self, table: str) -> Optional[int]:
        """
        Delete all records from Database Data. Returns number of rows if successful

        Parameters
        ----------
        table: str
            Database Table

        Returns
        -------
        Optional[int]
        """
        api_endpoint = urljoin(self.endpoint, f"{APIEndpoints.ADJUFTMENTS_BASE}/{table}")
        response = delete(url=api_endpoint, headers=self.headers)
        if response.status_code == 200:
            logger.info(f"Database Table Truncated: {table.title()}")
            return loads(response.content)
        else:
            raise AdjuftmentsError(response.text)

    @staticmethod
    def delete_imgur_image(delete_hash: str):
        """
        Delete an image from Imgur

        Parameters
        ----------
        delete_hash: str
            Image delete hash from Imgur

        Returns
        -------
        Response
        """
        imgur_api_url = f"https://api.imgur.com/3/image/{delete_hash}"
        headers = dict(Authorization=f"Client-ID {getenv('IMGUR_CLIENT_ID')}")
        response = delete(url=imgur_api_url,
                          headers=headers,
                          data=dict(),
                          files=list())
        if response.status_code != 200:
            raise AdjuftmentsError(response.text)
        return loads(response.content)

    def _handle_airtable_splitwise_request(self, airtable_expense: dict) -> None:
        """
        Handle all the required steps when a splitwise record needs to be interacted with
        from an expense record

        Parameters
        ----------
        airtable_expense : dict
            Expense as dict

        Returns
        -------
        None
        """
        record_id = airtable_expense["id"]
        splitwise_id = airtable_expense["splitwise_id"]
        # IF THIS IS AN UPDATE TO AN EXISTING RECORD...
        if splitwise_id is None:
            logger.info(f"New Splitwise Expense to be Created from Airtable: {record_id}")
            airtable_expense["splitwise"] = False
            splitwise_amount = airtable_expense["amount"]
            splitwise_transaction = airtable_expense["transaction"]
            splitwise_json = dict(cost=splitwise_amount,
                                  description=splitwise_transaction)
            new_splitwise_record = self._create_splitwise_data(record=splitwise_json)
            self._load_db_record(table="splitwise", record=new_splitwise_record)
            updated_airtable_record = airtable_expense.copy()
            updated_airtable_record["splitwise_id"] = new_splitwise_record["id"]
            updated_airtable_record["amount"] = new_splitwise_record["transaction_balance"]
            self._upsert_airtable_expense(airtable_expense=updated_airtable_record)
        else:
            logger.info("Splitwise ID Field is populated. "
                        f"Skipping expense creation: {splitwise_id}")
            existing_splitwise_expense = self._get_db_record(table="splitwise",
                                                             record_id=splitwise_id)
            if existing_splitwise_expense is None:
                logger.warning(f"No matching splitwise expense found: {splitwise_id} ."
                               "Overriding with NULL")
                airtable_expense["splitwise_id"] = None
            airtable_expense["splitwise"] = False
            self._upsert_airtable_expense(airtable_expense=airtable_expense)

    def _handle_airtable_delete_request(self, airtable_expense: dict):
        """
        Handle all the required steps when an airtable record needs to be deleted

        Parameters
        ----------
        airtable_expense : dict
            Expense as dict

        Returns
        -------
        None
        """
        record_id = airtable_expense["id"]
        splitwise_id = airtable_expense["splitwise_id"]
        if splitwise_id is not None:
            # DELETE FROM SPLITWISE
            self._delete_splitwise_data(record_id=splitwise_id)
            # DELETE SPLITWISE RECORD FROM DB
            self._delete_db_record(table="splitwise", record_id=splitwise_id)
        # DELETE EXPENSE RECORD FROM DB
        expense_record_to_delete = self._get_db_record(table="expenses",
                                                       record_id=record_id)
        if expense_record_to_delete is None:
            logger.info(f"Expense record not found in database for delete: {record_id}")
        else:
            expense_record_to_delete = self._delete_db_record(table="expenses",
                                                              record_id=record_id)
            logger.info(f"Expense deleted from database: {expense_record_to_delete['id']}")
        # FINALLY DELETE FROM AIRTABLE
        self._delete_airtable_data(table="expenses", record_id=record_id)

    @classmethod
    def _generate_splitwise_manifest(cls, data_array: List[dict]) -> Tuple[List[dict]]:
        """
        Generate a Manifest to update Airtable and Database

        Parameters
        ----------
        data_array: List[dict]
            Array of splitwise records

        Returns
        -------
        Tuple[List[dict]]
            (publish_manifest, delete_manifest)
        """
        publish_manifest = list()
        delete_manifest = list()

        for splitwise_expense in data_array:
            transaction_description = AdjuftmentsEncoder.parse_adjuftments_description(
                description=splitwise_expense["description"],
                default_string="Splitwise")
            transaction_amount = splitwise_expense["transaction_balance"]
            transaction_date_iso = splitwise_expense["date"]
            local_timezone = timezone(getenv("TZ", default="America/Denver"))
            transaction_date_local = datetime.fromisoformat(transaction_date_iso[:-1]).replace(
                tzinfo=timezone("UTC")).astimezone(local_timezone).replace(
                hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=None)
            splitwise_id = splitwise_expense["id"]

            if splitwise_expense["payment"] is False and splitwise_expense["deleted"] is False:
                airtable_dict = dict(amount=transaction_amount,
                                     category="Splitwise",
                                     date=transaction_date_local,
                                     imported=False,
                                     transaction=transaction_description,
                                     splitwise=False,
                                     splitwise_id=splitwise_id,
                                     account=None,
                                     delete=False)
                reencoded_dict = AdjuftmentsEncoder.parse_object(obj=airtable_dict)
                publish_manifest.append(reencoded_dict)
            elif splitwise_expense["deleted"] is True:
                delete_manifest.append(splitwise_expense)

        return publish_manifest, delete_manifest

    ######################################
    # CLEAN START FUNCTIONS
    ######################################

    def _build_database(self, drop_all: bool = False) -> None:
        """
        Build out the database using the API Endpoint

        Parameters
        ----------
        drop_all: bool
            Whether to drop and recreate all tables

        Returns
        -------
        None
        """
        api_endpoint = urljoin(self.endpoint, APIEndpoints.ADMIN_DATABASE_BUILD)
        response = post(url=api_endpoint,
                        json=dict(drop_all=drop_all),
                        headers=self.headers)
        if response.status_code != 200:
            raise AdjuftmentsError(response.text)
        return loads(response.content)

    def _clean_start(self, run: bool = True) -> None:
        """
        Refresh all database Data!

        Parameters
        ----------
        run: bool
            Whether to actually run

        Returns
        -------
        None
        """
        if run is True:
            self._clean_start_database_users()
            self._clean_start_budgets_data()
            self._clean_start_categories_data()
            self._clean_start_dashboard_data()
            self._clean_start_miscellaneous_data()
            self._clean_start_splitwise_data()
            self._clean_start_accounts_data()
            self._clean_start_expenses_data()
            self._clean_start_historic_expenses_data()  # MUST GO AFTER EXPENSES
            self._clean_start_stocks_data()

    def _clean_start_database_users(self):
        """
        Set up the Database with original users
        """
        api_endpoint = urljoin(self.endpoint, APIEndpoints.ADMIN_USERS)
        admin_user = post(url=api_endpoint, headers=None,
                          json={"clean_start": True})
        assert admin_user.status_code == 200
        return admin_user

    def _clean_start_expenses_data(self):
        """
        Get and process some expenses data
        """
        self._truncate_db_table(table="expenses")
        clean_formula = "AND({Imported}=True(), {Delete}=False())"
        clean_data_filter = dict(formula=clean_formula)
        data_array = self._get_airtable_data(table="expenses", params=clean_data_filter)
        self._load_db_data(table="expenses", data_array=data_array)
        self.refresh_dashboard(updated_data=True)

    def _clean_start_historic_expenses_data(self):
        """
        Get and process some expenses data
        """
        historic_expenses_data = list()
        self._truncate_db_table(table="historic_expenses")
        for year, historic_base in AirtableConfig.HISTORIC_BASES.items():
            historic_expenses_data += self._get_airtable_data(
                table="expenses",
                params=dict(airtable_base=historic_base))
        current_years_data = self._get_db_data(table="expenses")
        self._load_db_data(table="historic_expenses",
                           data_array=historic_expenses_data + current_years_data)

    def _clean_start_splitwise_data(self):
        """
        Get and Process some Splitwise Data
        """
        splitwise_array = self._get_splitwise_data(params=None)
        self._load_db_data(table="splitwise", data_array=splitwise_array)

    def _clean_start_budgets_data(self):
        """
        Get and process some budgets data
        """
        data_array = self._get_airtable_data(table="budgets", params=None)
        self._load_db_data(table="budgets", data_array=data_array)

    def _clean_start_categories_data(self):
        """
        Get and process some categories data
        """
        data_array = self._get_airtable_data(table="categories", params=None)
        self._load_db_data(table="categories", data_array=data_array)

    def _clean_start_dashboard_data(self):
        """
        Get and process some dashboard data
        """
        data_array = self._get_airtable_data(table="dashboard", params=None)
        for dashboard_record in data_array:
            if dashboard_record["measure"] == "Splitwise Balance":
                former_value = dashboard_record["value"]
                splitwise_balance = self._get_splitwise_balance()
                formatted_balance = AdjuftmentsEncoder.format_float(amount=splitwise_balance,
                                                                    float_format="money")
                dashboard_record["value"] = formatted_balance
                if former_value != formatted_balance:
                    self._update_airtable_record(table="dashboard",
                                                 record_id=dashboard_record["id"],
                                                 fields={"Value": str(formatted_balance)})
        self._load_db_data(table="dashboard", data_array=data_array)

    def _clean_start_miscellaneous_data(self):
        """
        Get and process some miscellaneous data
        """
        data_array = self._get_airtable_data(table="miscellaneous", params=None)
        self._load_db_data(table="miscellaneous", data_array=data_array)

    def _clean_start_stocks_data(self):
        """
        Get and process some stocks data
        """
        data_array = self._get_airtable_data(table="stocks", params=None)
        self._load_db_data(table="stocks", data_array=data_array)
        self.refresh_stocks_data()

    def _clean_start_accounts_data(self):
        """
        Get and process some stocks data
        """
        data_array = self._get_airtable_data(table="accounts", params=None)
        savings_default = list()
        checking_accounts = list()
        for data_value in data_array:
            if data_value["type"] == "Checking":
                checking_accounts.append(data_value["id"])
            elif data_value["default"] is True and data_value["type"] == "Savings":
                savings_default.append(data_value["id"])
        try:
            assert len(savings_default) == 1 and len(checking_accounts) == 1
        except AssertionError:
            raise AdjuftmentsError("Make sure a single Savings and Single "
                                   "Expense Account is marked as default")
        self._load_db_data(table="accounts", data_array=data_array)

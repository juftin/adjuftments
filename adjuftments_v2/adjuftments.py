#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Adjuftments High Level Functions
"""

from datetime import datetime
from hashlib import sha256
from json import loads
from json.decoder import JSONDecodeError
import logging
from os import getenv
from typing import List, Optional, Tuple
from urllib.parse import urljoin, urlunparse

from pytz import timezone, UTC
from requests import delete, get, post, Response

from adjuftments_v2.config import AirtableConfig
from adjuftments_v2.config import APIEndpoints
from adjuftments_v2.utils import AdjuftmentsEncoder

logger = logging.getLogger(__name__)


class AdjuftmentsError(Exception):
    """
    Base Exception
    """
    pass


class Adjuftments(object):
    """
    The Key Adjuftments SDK
    """

    def __init__(self, endpoint: str, api_token: str,
                 port: int = 5000, https: bool = False):
        """
        Store the internal endpoint

        Parameters
        ----------
        endpoint: str
        """
        self.scheme = "http" if https is False else "http"
        self.net_loc = endpoint if port is None else f"{endpoint}:{port}"

        self.port = port
        url_components = (self.scheme, self.net_loc, "", "", "", "")
        self.endpoint = urlunparse(components=url_components)
        self.headers = dict(Authorization=f"Bearer {api_token}")

    def __repr__(self) -> str:
        """
        String Representation
        """
        return f"<Adjuftments: {self.endpoint}>"

    def prepare_database(self, clean_start: bool = False):
        """
        Generate the Initial Database
        """
        if clean_start is True:
            logger.info("Initiating Clean Database Refresh")
            self._build_database(drop_all=True)
            self._clean_start(run=True)
        elif str(clean_start).lower() == "auto":
            logger.info("Initializing Database")
            try:
                data_size = len(self._get_db_data(table="expenses", params=dict(limit=1)))
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

    # REFRESH

    def refresh_dashboard(self, splitwise_balance: float = None) -> None:
        """
        Refresh the Adjuftments Dashboard

        Parameters
        ----------
        splitwise_balance : float
            Splitwise Balance to Update the Dashboard with

        Returns
        -------
        None
        """
        api_endpoint = urljoin(self.endpoint, APIEndpoints.DASHBOARD_GENERATOR)
        response = post(url=api_endpoint,
                        json=dict(splitwise_balance=splitwise_balance),
                        headers=self.headers)
        if response.status_code != 200:
            logger.error(response.text)
            raise AdjuftmentsError(response.text)
        response_content = loads(response.content)["manifest"]
        for updated_record in response_content:
            logger.info(f"Updated Dashboard: {updated_record['measure']} - "
                        f"{updated_record['value']}")
        return response_content

    def refresh_splitwise_data(self) -> Optional[float]:
        """
        Refresh the Splitwise table with the most recent data. Return an updated balance if
        new updates exist

        Returns
        -------
        float
        """

        recent_data = self._get_new_splitwise_data()
        logger.info(f"Data Ingestion: Splitwise: {len(recent_data)} records")
        if len(recent_data) > 0:
            self._load_db_data(table="splitwise", data_array=recent_data)
            splitwise_balance = self._get_splitwise_balance()
        else:
            splitwise_balance = None

        success_manifest, delete_manifest = self._generate_splitwise_manifest(
            data_array=recent_data)
        for airtable_record in success_manifest:
            response = self._create_airtable_data(table="expenses",
                                                  record=airtable_record)
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
        Refresh the Airtable data with the most recent data

        Returns
        -------
        int
            Returns the number of new records for update
        """
        latest_airtable_data = self._get_new_airtable_expenses_data()
        logger.info(f"Data Ingestion: Airtable: {len(latest_airtable_data)} records")
        # LOOP THROUGH NEW DATA
        for airtable_expense in latest_airtable_data:
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
                    logger.critical("No matching splitwise expense found: "
                                    f"{airtable_expense['splitwise_id']}. "
                                    "Overriding with NULL")
                    airtable_expense["splitwise_id"] = None
                self._upsert_airtable_expenses(airtable_expense=airtable_expense)
            else:
                self._upsert_airtable_expenses(airtable_expense=airtable_expense)
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

        # GET

    def _get_airtable_data(self, table: str, params: dict = None):
        """
        Update a record in Airtable

        Parameters
        ----------
        table: str
        params: dict

        Returns
        -------
        Response
        """
        api_endpoint = urljoin(self.endpoint, f"{APIEndpoints.AIRTABLE_BASE}/{table}")
        response = get(url=api_endpoint, params=params, headers=self.headers)
        if response.status_code != 200:
            logger.error(response.text)
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

    def _get_splitwise_balance(self):
        """
        Get Splitwise Balance
        """
        api_endpoint = urljoin(self.endpoint, APIEndpoints.SPLITWISE_BALANCE)
        splitwise_response = get(url=api_endpoint, headers=self.headers)
        return loads(splitwise_response.content)["balance"]

    def _get_splitwise_data(self, params: dict = None):
        """
        Get and Process some Splitwise Data
        """
        api_endpoint = urljoin(self.endpoint, APIEndpoints.SPLITWISE_EXPENSES)
        splitwise_response = get(url=api_endpoint, params=params, headers=self.headers)
        return loads(splitwise_response.content)

    def _get_db_record(self, table: str, record_id: str):
        """
        Get and Process some Database Data
        """
        api_endpoint = urljoin(self.endpoint,
                               f"{APIEndpoints.ADJUFTMENTS_BASE}/{table}/{record_id}")
        splitwise_response = get(url=api_endpoint, headers=self.headers)
        if splitwise_response.status_code == 200:
            return loads(splitwise_response.content)
        else:
            return None

    def _get_db_data(self, table: str, params: dict = None):
        """
        Get and Process some Database Data
        """
        api_endpoint = urljoin(self.endpoint, f"{APIEndpoints.ADJUFTMENTS_BASE}/{table}")
        splitwise_response = get(url=api_endpoint, params=params, headers=self.headers)
        return loads(splitwise_response.content)

    def _get_current_months_categories(self):
        """
        Get the current months expenses from the database
        """
        api_endpoint = urljoin(self.endpoint, APIEndpoints.EXPENSE_CATEGORIES)
        splitwise_response = get(url=api_endpoint, headers=self.headers)
        return loads(splitwise_response.content)

    def _get_splitwise_timestamp(self) -> datetime:
        """
        Get the latest modified timestamp from splitwise database table

        Returns
        -------
        datetime
        """
        api_endpoint = urljoin(self.endpoint, APIEndpoints.SPLITWISE_UPDATED_AT)
        response = get(url=api_endpoint,
                       headers=self.headers)
        if response.status_code == 200:
            return loads(response.content)
        else:
            raise AdjuftmentsError(response.text)
        return loads(response.content)

    def _get_new_splitwise_data(self) -> List[dict]:
        """
        Get the latest data from splitwise

        Returns
        -------
        splitwise_data: List[dict]
        """
        max_splitwise_timestamp = self._get_splitwise_timestamp()
        params = dict(updated_after=max_splitwise_timestamp["updated_after"])
        recent_data = self._get_splitwise_data(params=params)
        return recent_data

    def _get_stock_ticker(self, ticker: str) -> dict:
        """
        Get the Stock Price object for a ticker

        Parameters
        ----------
        ticker: str

        Returns
        -------
        dict
        """
        api_endpoint = urljoin(self.endpoint, f"{APIEndpoints.STOCK_TICKER_API}/{ticker.lower()}")
        response = get(url=api_endpoint,
                       headers=self.headers)
        if response.status_code == 200:
            return loads(response.content)
        else:
            raise AdjuftmentsError(response.text)

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

    # LOAD

    def _load_db_record(self, table: str, record: dict) -> None:
        """
        Load record to database

        Parameters
        ----------
        table: str
        record: dict

        Returns
        -------
        None
        """
        api_endpoint = urljoin(self.endpoint, f"{APIEndpoints.ADJUFTMENTS_BASE}/{table}")
        response = post(url=api_endpoint, json=record, headers=self.headers)
        if response.status_code != 200:
            logger.error(response.text)
            raise AdjuftmentsError(response.text)
        response_content = loads(response.content)
        logger.info(f"Upserted new {table} DB Record: {response_content['id']}")
        return response

    def _load_db_data(self, table: str, data_array: List[dict]) -> None:
        """
        Load data array to airtable

        Parameters
        ----------
        table: str
        data_array: List[str]

        Returns
        -------
        None
        """
        if isinstance(data_array, dict):
            data_array = [data_array]
        for expense_record in data_array:
            self._load_db_record(table=table, record=expense_record)

    # UPDATE / CREATE

    def _update_airtable_record(self, table: str, record_id: str, fields: dict):
        """
        Update a record in Airtable

        Parameters
        ----------
        table: str
        record_id: str
        fields: dict

        Returns
        -------
        Response
        """
        api_endpoint = urljoin(self.endpoint, f"{APIEndpoints.AIRTABLE_BASE}/{table}/{record_id}")
        response = post(url=api_endpoint, json=fields, headers=self.headers)
        if response.status_code != 200:
            logger.error(response.text)
            raise AdjuftmentsError(response.text)
        return response

    def _create_airtable_data(self, table: str, record: dict = None):
        """
        Create a record in Airtable

        Parameters
        ----------
        table: str
        record: dict

        Returns
        -------
        Response
        """
        api_endpoint = urljoin(self.endpoint, f"{APIEndpoints.AIRTABLE_BASE}/{table}")
        response = post(url=api_endpoint, json=record, headers=self.headers)
        if response.status_code != 200:
            logger.error(response.text)
            raise AdjuftmentsError(response.text)
        response_content = loads(response.content)
        return response_content

    def _create_splitwise_data(self, record: dict):
        """
        Create an expense in Splitwise. Requires "cost" and "description"
        fields to be passed in record

        Parameters
        ----------
        table: str
        record: dict

        Returns
        -------
        Response
        """
        api_endpoint = urljoin(self.endpoint, APIEndpoints.SPLITWISE_EXPENSES)
        response = post(url=api_endpoint, json=record, headers=self.headers)
        if response.status_code != 200:
            logger.error(response.text)
            raise AdjuftmentsError(response.text)
        response_content = loads(response.content)
        return response_content

    def _create_imgur_image(self, image_data: dict) -> dict:
        """
        Create an expense in Splitwise. Requires "cost" and "description"
        fields to be passed in record

        Parameters
        ----------
        table: str
        record: dict

        Returns
        -------
        Response
        """
        imgur_api_url = "https://api.imgur.com/3/image"
        headers = dict(Authorization=f"Client-ID {getenv('IMGUR_CLIENT_ID')}")
        response = post(url=imgur_api_url,
                        headers=headers,
                        data=image_data,
                        files=list())
        if response.status_code != 200:
            logger.error(response.text)
            raise AdjuftmentsError(response.text)
        response_content = loads(response.content)
        return response_content

    def _upsert_airtable_expenses(self, airtable_expense: dict):
        """
        Upsert a record into Airtable as well as the database

        Returns
        -------

        """
        record_id = airtable_expense["id"]
        if airtable_expense["splitwise"] is True:
            logger.error(f"This record shouldn't have Splitwise enabled {airtable_expense}")
            raise SystemError(f"This record shouldn't have Splitwise enabled {airtable_expense}")
        # UPSERT RECORD INTO DATABASE
        updated_record = self._prepare_expenses_record_for_upsert(record=airtable_expense)
        updated_record = AdjuftmentsEncoder.parse_object(obj=updated_record)
        self._load_db_record(table="expenses", record=updated_record)
        updated_record.pop("created_at")
        updated_record.pop("id")
        self._update_airtable_record(table="expenses", record_id=record_id,
                                     fields=updated_record)

    @classmethod
    def _prepare_expenses_record_for_upsert(cls, record: dict) -> dict:
        """
        Set Important Fields on a dict

        Parameters
        ----------
        record: dict

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
        return updated_record

    # DELETE

    def _delete_airtable_data(self, table: str, record_id: str) -> Response:
        """
        Delete a record from airtable

        Parameters
        ----------
        table
        record_id

        Returns
        -------
        Response
        """
        api_endpoint = urljoin(self.endpoint, f"{APIEndpoints.AIRTABLE_BASE}/{table}/{record_id}")
        response = delete(url=api_endpoint, headers=self.headers)
        if response.status_code == 200:
            logger.info(f"Airtable Record Deleted: {table.title()} - {record_id}")
            return loads(response.content)
        else:
            logger.error(response.text)
            return None

    def _delete_splitwise_data(self, record_id: str) -> Response:
        """
        Delete a record from Splitwise

        Parameters
        ----------
        record_id

        Returns
        -------
        Response
        """
        api_endpoint = urljoin(self.endpoint, f"{APIEndpoints.SPLITWISE_EXPENSES}/{record_id}")
        response = delete(url=api_endpoint, headers=self.headers)
        if response.status_code == 200:
            logger.info(f"Splitwise Record Deleted: {record_id}")
            return loads(response.content)
        else:
            logger.error(response.text)
            return None

    def _delete_db_record(self, table: str, record_id: str):
        """
        Delete some Database Data

        Parameters
        ----------
        table
        record_id

        Returns
        -------
        Response
        """
        api_endpoint = urljoin(self.endpoint,
                               f"{APIEndpoints.ADJUFTMENTS_BASE}/{table}/{record_id}")
        response = delete(url=api_endpoint, headers=self.headers)
        if response.status_code == 200:
            logger.info(f"Database Record Deleted: {table.title()} - {record_id}")
            return loads(response.content)
        else:
            logger.error(response.text)
            return None

    def _delete_imgur_image(self, delete_hash: str):
        """
        Delete some Database Data

        Parameters
        ----------
        table
        record_id

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
            logger.error(response.text)
            raise AdjuftmentsError(response.text)
        response_content = loads(response.content)
        return response_content

    def _handle_airtable_splitwise_request(self, airtable_expense: dict):
        """
        Handle when a record needs to be deleted.

        Returns
        -------

        """
        record_id = airtable_expense["id"]
        splitwise_id = airtable_expense["splitwise_id"]
        # IF THIS IS AN UPDATE TO AN EXISTING RECORD...
        if splitwise_id is None:
            logger.info(f"New Splitwise Expense to be Created from Airtable: {record_id}")
            # TODO: ENABLE THIS ONCE READY FOR PROD
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
            self._upsert_airtable_expenses(airtable_expense=updated_airtable_record)
        else:
            logger.info("Splitwise ID Field is populated. "
                        f"Skipping expense creation: {splitwise_id}")
            existing_splitwise_expense = self._get_db_record(table="splitwise",
                                                             record_id=splitwise_id)
            if existing_splitwise_expense is None:
                logger.critical(f"No matching splitwise expense found: {splitwise_id} ."
                                "Overriding with NULL")
                airtable_expense["splitwise_id"] = None
            airtable_expense["splitwise"] = False
            self._upsert_airtable_expenses(airtable_expense=airtable_expense)

    def _handle_airtable_delete_request(self, airtable_expense: dict):
        """
        Handle when a record needs to be deleted.

        Returns
        -------

        """
        record_id = airtable_expense["id"]
        splitwise_id = airtable_expense["splitwise_id"]
        if splitwise_id is not None:
            # DELETE FROM SPLITWISE
            # TODO: REENABLE THIS ONCE READY FOR PROD
            response = self._delete_splitwise_data(record_id=splitwise_id)
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
                tzinfo=UTC).astimezone(local_timezone).replace(
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
                                     delete=False)
                reencoded_dict = AdjuftmentsEncoder.parse_object(obj=airtable_dict)
                publish_manifest.append(reencoded_dict)
            elif splitwise_expense["deleted"] is True:
                delete_manifest.append(splitwise_expense)

        return publish_manifest, delete_manifest

    # CLEAN START

    def _build_database(self, drop_all: bool = False) -> None:
        """
        Build out the database using the API Endpoint

        Parameters
        ----------
        drop_all: bool
            Whether to drop and recreate all tables
        """
        api_endpoint = urljoin(self.endpoint, APIEndpoints.ADMIN_DATABASE_BUILD)
        response = post(url=api_endpoint,
                        json=dict(drop_all=drop_all),
                        headers=self.headers)
        if response.status_code == 200:
            return loads(response.content)
        else:
            raise AdjuftmentsError(response.text)

    def _clean_start(self, run: bool = True) -> None:
        """
        Refresh all Data!

        Parameters
        ----------
        run: bool

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
            self._clean_start_expenses_data()
            self._clean_start_historic_expenses_data()
            self._clean_start_stocks_data()

    def _clean_start_database_users(self):
        """
        Set up the Database with original users
        """
        api_endpoint = urljoin(self.endpoint, APIEndpoints.ADMIN_USERS)
        juftin_user = post(url=api_endpoint, headers=None,
                           json={"clean_start": True})
        assert juftin_user.status_code == 200
        return juftin_user

    def _clean_start_expenses_data(self):
        """
        Get and process some expenses data
        """
        clean_formula = "AND({Imported}=True(), {Delete}=False())"
        clean_data_filter = dict(formula=clean_formula)
        data_array = self._get_airtable_data(table="expenses", params=clean_data_filter)
        self._load_db_data(table="expenses", data_array=data_array)

    def _clean_start_historic_expenses_data(self):
        """
        Get and process some expenses data
        """
        historic_expenses_data = list()
        for year, historic_base in AirtableConfig.HISTORIC_BASES.items():
            historic_expenses_data += self._get_airtable_data(
                table="expenses",
                params=dict(airtable_base=historic_base))
        self._load_db_data(table="historic_expenses", data_array=historic_expenses_data)

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

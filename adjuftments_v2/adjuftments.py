#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Adjuftments High Level Functions
"""

from datetime import datetime, timedelta
from json import dumps, loads
import logging
from os import getenv
from typing import List, Tuple
from urllib.parse import urljoin, urlunparse

from pytz import timezone, UTC
from requests import delete, get, post, Response

from adjuftments_v2 import Airtable, Dashboard, database_connection, Splitwise
from adjuftments_v2.application import db
from adjuftments_v2.config import APIEndpoints
from adjuftments_v2.utils import AdjuftmentsEncoder

logger = logging.getLogger(__name__)


class Adjuftments(object):
    """
    The Key Adjuftments SDK
    """

    def __init__(self, endpoint: str, port: int = None, https: str = False):
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

    def prepare_database(self, clean_start: bool = False):
        """
        Generate the Initial Database
        """
        from adjuftments_v2.models import ALL_TABLES
        logger.info(f"Preparing Database: {len(ALL_TABLES)} table(s)")
        if not db.engine.dialect.has_schema(db.engine, "adjuftments"):
            db.engine.execute("CREATE SCHEMA adjuftments;")

        if clean_start is True:
            logger.info("Initiating Clean Database Refresh")
            db.drop_all()
            db.create_all()
            self._clean_start(run=clean_start)
        else:
            db.create_all()

        logger.info("Database Created")

    def refresh_dashboard(self) -> None:
        """
        Refresh the Adjuftments Dashboard

        Returns
        -------
        None
        """
        logger.info("Retrieving Data for Dashboard")
        clean_data_filter = dict(imported=True, delete=False)
        airtable_expenses_data = self._get_db_data(table="expenses", params=clean_data_filter)
        logger.info("Data retrieved, converting data to DataFrame")
        df = Airtable.expenses_as_df(expense_array=airtable_expenses_data)
        logger.info("Generating Internal Dashboard Update")
        dashboard_manifest = Dashboard.run_dashboard(dataframe=df)
        logger.info(f"{len(dashboard_manifest)} records to update in Airtable")
        for manifest_record in dashboard_manifest:
            update_fields = dict(Value=manifest_record["value"])
            self._update_airtable_record(table="dashboard",
                                         record_id=manifest_record["id"],
                                         fields=update_fields)
        logger.info("Dashboard Refresh Complete")

    def refresh_splitwise_data(self) -> None:
        """
        Refresh the Splitwise table with the most recent data

        Returns
        -------
        None
        """
        recent_data = self._get_new_splitwise_data()
        if len(recent_data) > 0:
            logger.info(f"Loading {len(recent_data)} new records to splitwise")
            self._load_db_data(table="splitwise", data_array=recent_data)
        success_manifest, delete_manifest = self._generate_splitwise_manifest(
            data_array=recent_data)
        for airtable_record in success_manifest:
            response = self._create_airtable_data(table="expenses",
                                                  record=airtable_record)
            logger.critical(response)
        #############################
        latest_airtable_data = self._get_new_airtable_expenses_data()
        logger.critical(f"{len(latest_airtable_data)} new Airtable records found to ingest")
        # LOOP THROUGH NEW DATA
        for airtable_expense in latest_airtable_data:
            record_id = airtable_expense["id"]
            splitwise_id = airtable_expense["splitwise_id"]
            # IF THE RECORD CONTAINS DELETE
            if airtable_expense["delete"] is True:
                if splitwise_id is not None:
                    # DELETE FROM SPLITWISE
                    # TODO: REENABLE THIS
                    # response = self._delete_splitwise_data(record_id=splitwise_id)
                    logger.critical(response)
                    # DELETE SPLITWISE RECORD FROM DB
                    self._delete_db_record(table="splitwise", record_id=splitwise_id)
                    logger.critical(response)
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
                response = self._delete_airtable_data(table="expenses", record_id=record_id)
                logger.critical(response)

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
            self._clean_start_budgets_data()
            self._clean_start_categories_data()
            self._clean_start_dashboard_data()
            self._clean_start_miscellaneous_data()
            self._clean_start_splitwise_data()
            self._clean_start_expenses_data()

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
        response = get(url=api_endpoint, params=params)
        assert response.status_code == 200
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

    def _get_splitwise_data(self, params: dict = None):
        """
        Get and Process some Splitwise Data
        """
        api_endpoint = urljoin(self.endpoint, APIEndpoints.SPLITWISE_EXPENSES)
        splitwise_response = get(url=api_endpoint, params=params)
        return loads(splitwise_response.content)

    def _get_db_record(self, table: str, record_id: str):
        """
        Get and Process some Database Data
        """
        api_endpoint = urljoin(self.endpoint,
                               f"{APIEndpoints.ADJUFTMENTS_BASE}/{table}/{record_id}")
        splitwise_response = get(url=api_endpoint)
        if splitwise_response.status_code == 200:
            return loads(splitwise_response.content)
        else:
            logger.error(splitwise_response.text)
            return None

    def _get_db_data(self, table: str, params: dict = None):
        """
        Get and Process some Database Data
        """
        api_endpoint = urljoin(self.endpoint, f"{APIEndpoints.ADJUFTMENTS_BASE}/{table}")
        splitwise_response = get(url=api_endpoint, params=params)
        return loads(splitwise_response.content)

    def _get_new_splitwise_data(self) -> List[dict]:
        """
        Get the latest data from splitwise

        Returns
        -------
        splitwise_data: List[dict]
        """
        max_splitwise_timestamp = database_connection.get_max_date(table="splitwise",
                                                                   date_column="updated_at",
                                                                   replace_none=True)
        # THE SPLITWISE SDK'S PARAMETER SHOULD BE CALLED updated_on_or_after
        new_data_updated_after = max_splitwise_timestamp + timedelta(microseconds=1)
        params = dict(updated_after=new_data_updated_after)
        recent_data = self._get_splitwise_data(params=params)
        return recent_data

    def _load_db_record(self, table: str, record: dict) -> None:
        """
        Load record to airtable

        Parameters
        ----------
        table: str
        record: List[str]

        Returns
        -------
        None
        """
        api_endpoint = urljoin(self.endpoint, f"{APIEndpoints.ADJUFTMENTS_BASE}/{table}")
        response = post(url=api_endpoint, json=record)
        assert response.status_code == 200
        response_content = loads(response.content)
        logger.info(f"Loaded new {table} DB Record: {response_content['id']}")
        return response

    def _load_db_data(self, table: str, data_array: List[str]) -> None:
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
        for expense_record in data_array:
            self._load_db_record(table=table, record=expense_record)

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
        response = post(url=api_endpoint, json=fields)
        assert response.status_code == 200
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
        response = post(url=api_endpoint, json=record)
        assert response.status_code == 200
        response_content = loads(response.content)
        return response_content

    def _create_splitwise_data(self, record: dict = None):
        """
        Create an expense in Splitwise

        Parameters
        ----------
        table: str
        record: dict

        Returns
        -------
        Response
        """
        api_endpoint = urljoin(self.endpoint, APIEndpoints.SPLITWISE_EXPENSES)
        response = post(url=api_endpoint, json=record)
        assert response.status_code == 200
        response_content = loads(response.content)
        return response_content

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
        response = delete(url=api_endpoint)
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
        response = delete(url=api_endpoint)
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
        response = delete(url=api_endpoint)
        if response.status_code == 200:
            logger.info(f"Database Record Deleted: {table.title()} - {record_id}")
            return loads(response.content)
        else:
            logger.error(response.text)
            return None

    def _clean_start_expenses_data(self):
        """
        Get and process some expenses data
        """
        clean_data_filter = dict(formula="AND({Imported}=True(), {Delete}=False())")
        data_array = self._get_airtable_data(table="expenses", params=clean_data_filter)
        self._load_db_data(table="expenses", data_array=data_array)

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
        self._load_db_data(table="dashboard", data_array=data_array)

    def _clean_start_miscellaneous_data(self):
        """
        Get and process some miscellaneous data
        """
        data_array = self._get_airtable_data(table="miscellaneous", params=None)
        self._load_db_data(table="miscellaneous", data_array=data_array)

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
            transaction_description = Splitwise.parse_splitwise_description(
                description=splitwise_expense["description"])
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
                airtable_dict_str = dumps(airtable_dict, cls=AdjuftmentsEncoder)
                reencoded_dict = loads(airtable_dict_str)
                publish_manifest.append(reencoded_dict)
            elif splitwise_expense["deleted"] is True:
                airtable_dict = dict(amount=transaction_amount,
                                     category="Splitwise",
                                     date=transaction_date_local,
                                     imported=False,
                                     transaction=transaction_description,
                                     splitwise=False,
                                     splitwise_id=splitwise_id,
                                     delete=True)
                airtable_dict_str = dumps(airtable_dict, cls=AdjuftmentsEncoder)
                reencoded_dict = loads(airtable_dict_str)
                delete_manifest.append(reencoded_dict)

        return publish_manifest, delete_manifest

#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
AirTable Configuration.
"""

import logging
from os import environ
from typing import Dict, List

from dotenv import load_dotenv
from numpy import bool_, datetime64, float64, object_

from .file_config import DOT_ENV_FILE_PATH

load_dotenv(DOT_ENV_FILE_PATH, override=True)
logger = logging.getLogger(__name__)


class AirtableConfig(object):
    """
    Airtable Config Object
    """
    AIRTABLE_API_KEY: str = environ["AIRTABLE_API_KEY"]
    AIRTABLE_BASE: str = environ["AIRTABLE_BASE"]

    HISTORIC_BASES: Dict[str, str] = dict()
    _historical_base_prefix = "AIRTABLE_HISTORICAL_BASE_"
    for _environment_variable in environ.keys():
        if all([_environment_variable.startswith(_historical_base_prefix),
                environ[_environment_variable] != ""]):
            _historical_year = _environment_variable.replace(_historical_base_prefix, "")
            HISTORIC_BASES[_historical_year] = environ[_environment_variable]


class AirtableColumnMapping(object):
    """
    Airtable -> SQL Column Mapping
    """
    EXPENSES: Dict[str, str] = dict(
        id="id",
        Amount="amount",
        Category="category",
        Date="date",
        Account="account",
        AccountName="account_name",
        Imported="imported",
        ImportedAt="imported_at",
        Transaction="transaction",
        UUID="uuid",
        Splitwise="splitwise",
        splitwiseID="splitwise_id",
        createdTime="created_at",
        Delete="delete",
        ModifiedAt="updated_at"
    )

    EXPENSES_REVERSE: Dict[str, str] = {value: key for key, value in EXPENSES.items()}

    EXPENSES_DTYPE_MAPPING: Dict[str, object] = dict(
        id=object_,
        amount=float64,
        category=object_,
        date=datetime64,
        account=object_,
        account_name=object_,
        imported=bool_,
        imported_at=datetime64,
        transaction=object_,
        uuid=object_,
        splitwise=bool_,
        splitwise_id="Int64",
        created_at=datetime64,
        delete=bool_,
        updated_at="datetime64[ns]",
    )

    EXPENSES_COLUMN_ORDERING: List[str] = [key for key, value in EXPENSES_DTYPE_MAPPING.items()]

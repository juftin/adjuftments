#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
AirTable Configuration.
"""

import logging
from os import environ, getenv
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
    _2020_AIRTABLE_BASE: str = (2020, getenv("AIRTABLE_BASE_2020", None))
    _2019_AIRTABLE_BASE: str = (2019, getenv("AIRTABLE_BASE_2019", None))
    _2018_AIRTABLE_BASE: str = (2018, getenv("AIRTABLE_BASE_2018", None))
    _HISTORIC_BASES_PREP: List[str] = [_2018_AIRTABLE_BASE,
                                       _2019_AIRTABLE_BASE,
                                       _2020_AIRTABLE_BASE]
    HISTORIC_BASES: Dict[str, str] = {str(year): base for (year, base) in _HISTORIC_BASES_PREP if
                                      base is not None}


class AirtableColumnMapping(object):
    """
    Airtable -> SQL Column Mapping
    """
    Expenses: Dict[str, str] = dict(
        id="id",
        Amount="amount",
        Category="category",
        Date="date",
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

    ExpensesReverse: Dict[str, str] = {value: key for key, value in Expenses.items()}

    EXPENSES_DTYPE_MAPPING: Dict[str, object] = dict(
        id=object_,
        amount=float64,
        category=object_,
        date=datetime64,
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

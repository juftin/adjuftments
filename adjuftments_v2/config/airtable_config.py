#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
AirTable Configuration.
"""

import logging
from os import environ, path
from pathlib import Path
from typing import Dict, List

from dotenv import load_dotenv
from numpy import bool_, datetime64, float64, object_

logger = logging.getLogger(__name__)

config_dir = Path(path.abspath(__file__)).parent
env_file = path.join(config_dir.parent.parent, '.env')
load_dotenv(env_file, override=True)


class AirtableConfig(object):
    """
    Airtable Config Object
    """
    AIRTABLE_API_KEY: str = environ["AIRTABLE_API_KEY"]
    AIRTABLE_BASE: str = environ["AIRTABLE_BASE"]


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
        Delete="delete"
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
        delete=bool_
    )

    EXPENSES_COLUMN_ORDERING: List[str] = [key for key, value in EXPENSES_DTYPE_MAPPING.items()]

#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
AirTable Configuration.
"""

from os import environ, path
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv

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
        Transaction="transaction",
        Amount="amount",
        Date="date",
        Category="category",
        Imported="imported",
        ImportedAt="imported_at",
        Delete="delete",
        UUID="uuid",
        Splitwise="splitwise",
        splitwiseID="splitwise_id"
    )

    ExpensesReverse: Dict[str, str] = {value: key for key, value in Expenses.items()}

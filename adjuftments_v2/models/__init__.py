#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Adjuftments Flask-SQLAlchemy Models
"""

from typing import Dict, List

from sqlalchemy import Table

from .budgets import BudgetsTable
from .categories import CategoriesTable
from .dashboard import DashboardTable
from .expenses import ExpensesTable
from .historic_expenses import HistoricExpensesTable
from .miscellaneous import MiscellaneousTable
from .splitwise import SplitwiseTable
from .stocks import StocksTable
from .users import UsersTable

# noinspection PyTypeChecker
ALL_TABLES: List[Table] = [
    BudgetsTable,
    CategoriesTable,
    DashboardTable,
    ExpensesTable,
    HistoricExpensesTable,
    MiscellaneousTable,
    SplitwiseTable,
    StocksTable,
    UsersTable
]

# PRIVATE TABLES NOT TO EXPOSE USING MODEL_FINDER
PRIVATE_TABLES: str = {UsersTable}
# noinspection PyTypeChecker
MODEL_FINDER: Dict[str, Table] = {table.__tablename__: table for table in
                                  (set(ALL_TABLES) - PRIVATE_TABLES)}

__all__ = [
    "BudgetsTable",
    "CategoriesTable",
    "DashboardTable",
    "ExpensesTable",
    "HistoricExpensesTable",
    "MiscellaneousTable",
    "SplitwiseTable",
    "StocksTable",
    "UsersTable",
    "MODEL_FINDER",
    "ALL_TABLES"
]

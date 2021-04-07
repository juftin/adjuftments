#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Adjuftments Flask-SQLAlchemy Models
"""

from typing import Dict, List

from sqlalchemy import Table

from .budgets_table import BudgetsTable
from .categories_table import CategoriesTable
from .dashboard_table import DashboardTable
from .expenses_table import ExpensesTable
from .historic_expenses_table import HistoricExpensesTable
from .miscellaneous_table import MiscellaneousTable
from .splitwise_table import SplitwiseTable
from .stocks_table import StocksTable
from .users_table import UsersTable

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

# PRIVATE TABLES NOT TO EXPOSE USING TABLE_FINDER
PRIVATE_TABLES: str = {UsersTable}
# noinspection PyTypeChecker
TABLE_FINDER: Dict[str, Table] = {table.__tablename__: table for table in
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
    "TABLE_FINDER",
    "ALL_TABLES"
]

#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Adjuftments Flask-SQLAlchemy Models
"""

from typing import Dict, List

from flask_sqlalchemy import Model

from .budgets import BudgetsTable
from .categories import CategoriesTable
from .dashboard import DashboardTable
from .expenses import ExpensesTable
from .historic_expenses import HistoricExpensesTable
from .job_scheduler import JobSchedulerTable
from .miscellaneous import MiscellaneousTable
from .splitwise import SplitwiseTable
from .stocks import StocksTable
from .users import UsersTable

# noinspection PyTypeChecker
ALL_TABLES: List[Model] = [
    BudgetsTable,
    CategoriesTable,
    DashboardTable,
    ExpensesTable,
    HistoricExpensesTable,
    JobSchedulerTable,
    MiscellaneousTable,
    SplitwiseTable,
    StocksTable,
    UsersTable
]
_private_data_tables = [UsersTable, JobSchedulerTable]
MODEL_FINDER: Dict[str, Model] = {table.__tablename__: table for table in
                                  (set(ALL_TABLES) - set(_private_data_tables))}

__all__ = [
    "BudgetsTable",
    "CategoriesTable",
    "DashboardTable",
    "ExpensesTable",
    "HistoricExpensesTable",
    "JobSchedulerTable",
    "MiscellaneousTable",
    "SplitwiseTable",
    "StocksTable",
    "UsersTable",
    "MODEL_FINDER"
]

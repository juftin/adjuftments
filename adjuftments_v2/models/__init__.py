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

ALL_TABLES: List[Model] = [
    BudgetsTable,
    CategoriesTable,
    DashboardTable,
    ExpensesTable,
    HistoricExpensesTable,
    MiscellaneousTable,
    SplitwiseTable,
    StocksTable,
    UsersTable,
    JobSchedulerTable
]

MODEL_FINDER: Dict[str, Model] = {
    "budgets": BudgetsTable,
    "categories": CategoriesTable,
    "dashboard": DashboardTable,
    "expenses": ExpensesTable,
    "historic_expenses": HistoricExpensesTable,
    "miscellaneous": MiscellaneousTable,
    "splitwise": SplitwiseTable,
    "stocks": StocksTable,
    "users": UsersTable
}

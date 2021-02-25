#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Adjuftments Flask-SQLAlchemy Models
"""

from .budgets import BudgetsTable
from .categories import CategoriesTable
from .dashboard import DashboardTable
from .expenses import ExpensesTable
from .miscellaneous import MiscellaneousTable
from .splitwise import SplitwiseTable

ALL_TABLES = [
    BudgetsTable,
    CategoriesTable,
    DashboardTable,
    ExpensesTable,
    MiscellaneousTable,
    SplitwiseTable
]

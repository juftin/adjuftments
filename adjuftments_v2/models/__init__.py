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
from .miscellaneous import MiscellaneousTable
from .splitwise import SplitwiseTable

ALL_TABLES: List[Model] = [
    BudgetsTable,
    CategoriesTable,
    DashboardTable,
    ExpensesTable,
    MiscellaneousTable,
    SplitwiseTable
]

MODEL_FINDER: Dict[str, Model] = {
    "budgets": BudgetsTable,
    "categories": CategoriesTable,
    "dashboard": DashboardTable,
    "expenses": ExpensesTable,
    "miscellaneous": MiscellaneousTable,
    "splitwise": SplitwiseTable
}

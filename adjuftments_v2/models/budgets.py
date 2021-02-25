#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from adjuftments_v2 import db


class BudgetsTable(db.Model):
    """
    Core Expenses Table
    """
    __tablename__ = "budgets"

    month = db.Column(db.String(32), primary_key=True, unique=True, nullable=False)
    proposed_budget = db.Column(db.Numeric(10, 2),
                                default=0.00, nullable=False)
    actual_budget = db.Column(db.Numeric(10, 2),
                              default=0.00, nullable=False)
    proposed_savings = db.Column(db.Numeric(10, 2),
                                 default=0.00, nullable=False)
    amount_saved = db.Column(db.Numeric(10, 2),
                             default=0.00, nullable=False)
    amount_spent = db.Column(db.Numeric(10, 2),
                             default=0.00, nullable=False)
    amount_earned = db.Column(db.Numeric(10, 2),
                              default=0.00, nullable=False)

    def __repr__(self):
        return f"<Budgets: {self.month}>"

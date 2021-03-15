#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from adjuftments_v2.application import db


class BudgetsTable(db.Model):
    """
    Core Expenses Table
    """
    __tablename__ = "budgets"
    __table_args__ = {"schema": "adjuftments"}

    id = db.Column(db.String(32), primary_key=True, unique=True, nullable=False)
    month = db.Column(db.String(32), unique=True, nullable=False, index=True)
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
    created_at = db.Column(db.DateTime(timezone="UTC"), nullable=False)

    def __repr__(self):
        return f"<{self.__tablename__}: {self.month}>"

    def to_dict(self) -> dict:
        """
        Return a flat dictionary with column mappings

        Returns
        -------
        dict
        """
        return dict(
            id=self.id,
            month=self.month,
            proposed_budget=self.proposed_budget,
            actual_budget=self.actual_budget,
            proposed_savings=self.proposed_savings,
            amount_saved=self.amount_saved,
            amount_spent=self.amount_spent,
            amount_earned=self.amount_earned,
            created_at=self.created_at
        )

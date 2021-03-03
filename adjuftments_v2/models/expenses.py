#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from adjuftments_v2.application import db


class ExpensesTable(db.Model):
    """
    Core Expenses Table
    """
    __tablename__ = "expenses"
    __table_args__ = {"schema": "adjuftments"}

    id = db.Column(db.String(32), primary_key=True, unique=True, nullable=False)
    amount = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    category = db.Column(db.String(32), nullable=False)
    date = db.Column(db.DateTime(timezone="UTC"), nullable=False)
    imported = db.Column(db.Boolean, default=False, nullable=False)
    imported_at = db.Column(db.DateTime(timezone="UTC"), nullable=True)
    transaction = db.Column(db.String(512), nullable=False)
    uuid = db.Column(db.String(128), nullable=True)
    splitwise = db.Column(db.Boolean, default=False, nullable=False)
    splitwise_id = db.Column(db.Integer(), db.ForeignKey("adjuftments.splitwise.id"),
                             nullable=True)
    created_at = db.Column(db.DateTime(timezone="UTC"), nullable=False)

    def __repr__(self):
        return f"<{self.__tablename__}: {self.id}>"

    def to_dict(self) -> dict:
        """
        Return a flat dictionary with column mappings

        Returns
        -------
        dict
        """
        return dict(
            id=self.id,
            amount=self.amount,
            category=self.category,
            date=self.date,
            imported=self.imported,
            imported_at=self.imported_at,
            transaction=self.transaction,
            uuid=self.uuid,
            splitwise=self.splitwise,
            splitwise_id=self.splitwise_id,
            created_at=self.created_at
        )

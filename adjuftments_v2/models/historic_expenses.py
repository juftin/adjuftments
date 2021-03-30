#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from sqlalchemy import func

from adjuftments_v2.application import db


class HistoricExpensesTable(db.Model):
    """
    Extension of the Expenses Table for storing historic data
    """
    __tablename__ = "historic_expenses"
    __table_args__ = {"schema": "adjuftments"}

    id = db.Column(db.String(32), primary_key=True, unique=True, nullable=False, index=True)
    amount = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    category = db.Column(db.String(32), nullable=False)
    date = db.Column(db.DateTime(timezone="UTC"), nullable=False)
    imported = db.Column(db.Boolean, default=False, nullable=False)
    imported_at = db.Column(db.DateTime(timezone="UTC"), nullable=True)
    transaction = db.Column(db.String(512), nullable=False)
    uuid = db.Column(db.String(128), nullable=True)
    splitwise = db.Column(db.Boolean, default=False, nullable=False)
    splitwise_id = db.Column(db.Integer(), nullable=True)
    created_at = db.Column(db.DateTime(timezone="UTC"), nullable=False)
    delete = db.Column(db.Boolean, default=False, nullable=False)
    updated_at = db.Column(db.DateTime(timezone="UTC"), nullable=False,
                           server_default=func.now(timezone="utc"),
                           onupdate=func.now(timezone="utc"))

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
            created_at=self.created_at,
            delete=self.delete,
            updated_at=self.updated_at
        )

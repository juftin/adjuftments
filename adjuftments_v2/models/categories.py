#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from adjuftments_v2.application import db


class CategoriesTable(db.Model):
    """
    Core Dashboard Table
    """
    __tablename__ = "catgories"
    __table_args__ = {"schema": "adjuftments"}

    id = db.Column(db.String(32), primary_key=True, unique=True, nullable=False)
    category = db.Column(db.String(32), unique=True, nullable=False, index=True)
    amount_spent = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    percent_of_total = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    created_at = db.Column(db.DateTime(timezone="UTC"), nullable=False)

    def __repr__(self):
        return f"<{self.__tablename__}: {self.category}>"

    def to_dict(self) -> dict:
        """
        Return a flat dictionary with column mappings

        Returns
        -------
        dict
        """
        return dict(
            id=self.id,
            category=self.category,
            amount_spent=self.amount_spent,
            percent_of_total=self.percent_of_total,
            created_at=self.created_at
        )

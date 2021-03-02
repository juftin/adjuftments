#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from adjuftments_v2 import db


class CategoriesTable(db.Model):
    """
    Core Dashboard Table
    """
    __tablename__ = "catgories"
    __table_args__ = {"schema": "adjuftments"}

    id = db.Column(db.String(32), primary_key=True, unique=True, nullable=False)
    category = db.Column(db.String(32), unique=True, nullable=False)
    amount_spent = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    percent_of_total = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    created_at = db.Column(db.DateTime(timezone="UTC"), nullable=False)

    def __repr__(self):
        return f"<Categories: {self.category}>"

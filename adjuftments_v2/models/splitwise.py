#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from adjuftments_v2 import db


class SplitwiseTable(db.Model):
    """
    Core Splitwise Table
    """
    __tablename__ = "splitwise"

    id = db.Column(db.Integer(), primary_key=True, unique=True, nullable=False)
    transaction_balance = db.Column(db.Numeric(10, 2), nullable=False)
    category = db.Column(db.String(32), nullable=False)
    cost = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime(timezone="UTC"), nullable=False)
    created_by = db.Column(db.Integer(), nullable=False)
    currency = db.Column(db.String(32), nullable=False)
    date = db.Column(db.DateTime(timezone="UTC"), nullable=False)
    deleted = db.Column(db.Boolean, nullable=False)
    deleted_at = db.Column(db.DateTime(timezone="UTC"), nullable=True)
    description = db.Column(db.String(512), nullable=False)
    payment = db.Column(db.Boolean, nullable=False)
    updated_at = db.Column(db.DateTime(timezone="UTC"), nullable=False)

    def __repr__(self):
        return f"<Splitwise {self.id}>"

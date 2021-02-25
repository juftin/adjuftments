#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from adjuftments_v2 import db


class DashboardTable(db.Model):
    """
    Core Dashboard Table
    """
    __tablename__ = "dashboard"

    measure = db.Column(db.String(32), primary_key=True, unique=True, nullable=False)
    value = db.Column(db.String(64), nullable=True)

    def __repr__(self):
        return f"<Dashboard: {self.measure}>"

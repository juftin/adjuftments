#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from adjuftments_v2 import db


class MiscellaneousTable(db.Model):
    """
    Core Miscellaneous Table
    """
    __tablename__ = "miscellaneous"

    measure = db.Column(db.String(32), primary_key=True, unique=True, nullable=False)
    value = db.Column(db.String(64), nullable=True)

    def __repr__(self):
        return f"<Miscellaneous: {self.measure}>"

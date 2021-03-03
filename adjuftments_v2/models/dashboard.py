#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from adjuftments_v2.application import db


class DashboardTable(db.Model):
    """
    Core Dashboard Table
    """
    __tablename__ = "dashboard"
    __table_args__ = {"schema": "adjuftments"}

    id = db.Column(db.String(32), primary_key=True, unique=True, nullable=False)
    measure = db.Column(db.String(32), unique=True, nullable=False)
    value = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime(timezone="UTC"), nullable=False)

    def __repr__(self):
        return f"<{self.__tablename__}: {self.measure}>"

    def to_dict(self) -> dict:
        """
        Return a flat dictionary with column mappings

        Returns
        -------
        dict
        """
        return dict(
            id=self.id,
            measure=self.measure,
            value=self.value,
            created_at=self.created_at
        )

#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Generic Errors for Adjuftments
"""

import logging

logger = logging.getLogger(__name__)


class AdjuftmentsError(Exception):
    """
    Refresh Error
    """
    pass


class AdjuftmentsRefreshError(Exception):
    """
    Refresh Error
    """
    pass

#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Adjuftments File Configurations
"""

from os.path import abspath, join
from pathlib import Path

DOT_ENV_FILE_PATH = join(Path(abspath(__file__)).parent.parent.parent, ".env")

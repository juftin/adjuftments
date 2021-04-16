#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Gunicorn Configuration File
"""

bind = "0.0.0.0:5000"  # The socket to bind.
workers = 2  # The number of worker processes for handling requests
wsgi_app = "adjuftments.rest_api:app"  # WSGI application path
reload = True  # Restart workers when code changes.
timeout = 60  # Workers silent for more than this many seconds are killed and restarted
accesslog = "-"  # The Access log file to write to ( '-' = stdout)
access_log_format = '%(t)s %(r)s %(s)s %(h)s'  # Logging Format

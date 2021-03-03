#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)
from json import loads

from requests import delete, get, post

# airtable_response = get(url="http://localhost:5000/api/1.0/airtable/expenses")
# for response_content in loads(airtable_response.content):
#     response = post(url="http://localhost:5000/api/1.0/adjuftments/expenses",
#                     json=response_content)

# content = dict(cost=100.00, description="Splitwise Testing 6 - Sorry for Spamming You")
# response = post(url="http://localhost:5000/api/1.0/splitwise/expenses",
#                 json=content)


another_url = "http://localhost:5000/api/1.0/airtable/expenses"
# response = get(url=another_url)
# response_content = loads(response.content)
response_2 = post(url=another_url, json={"uuid": "12232343252"})

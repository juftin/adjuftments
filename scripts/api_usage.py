#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from json import loads

from requests import get

from adjuftments_v2 import Splitwise

response = get(url="http://localhost:5000/api/1.0/airtable/expenses",
               params=dict(formula="OR({Imported}=True(), {Delete}=True())"))
response_content = loads(response.content)

response2 = get(url="http://localhost:5000/api/1.0/splitwise/expenses",
                params=dict(limit=100))
response_content2 = loads(response2.content)
df = Splitwise.expenses_as_df(response_content2)

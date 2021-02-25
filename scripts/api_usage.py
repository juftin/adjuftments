#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from json import loads

from pandas import DataFrame
from pandas.io.json import json_normalize
from requests import get

response = get(url="http://localhost:5000/api/1.0/airtable/expenses/",
               params={})
response_content = loads(response.content)

df = DataFrame(json_normalize(data=response_content, record_prefix=None))
df.columns = df.columns.str.replace("fields.", "")

for column in df.columns:
    print(column)
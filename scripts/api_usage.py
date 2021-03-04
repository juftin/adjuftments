#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)
from datetime import datetime
from json import loads

from requests import get

from adjuftments_v2 import Airtable, Dashboard
from adjuftments_v2.models import BudgetsTable

airtable_response = get(url="http://localhost:5000/api/1.0/adjuftments/expenses")
df = Airtable.expenses_as_df(expense_array=loads(airtable_response.content))
df2 = Dashboard._balance_df(dataframe=df, starting_home_balance=0,
                            starting_miscellaneous_balance=0,
                            starting_shared_balance=0, starting_checking_balance=0)
Dashboard._get_monthly_totals(dataframe=df2)
# account_balances = Dashboard._get_account_balances(dataframe=df2)
# response = BudgetsTable.query.filter_by(month=datetime.now().strftime(format="%B")).first()
# print(response.to_dict())

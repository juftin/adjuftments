#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Dashboard Configuration.
"""

from typing import Dict


class DashboardConfig(object):
    """
    Dashboard Column Mapping Configuration
    """
    DICT_TO_DASHBOARD: Dict[str, str] = {
        "amount_under_budget": "Under Budget",
        "checking_balance": "Checking Balance",
        "amount_to_save": "Amount to Save",
        "amount_budget_left": "Budget Left",
        "resulting_savings": "Resulting Savings",
        "monthly_expenses": "Monthly Spending",
        "monthly_savings": "Monthly Savings",
        "total_savings": "Savings Balance",
        "net_worth": "Net Worth",
        "splitwise_balance": "Splitwise Balance",
        "total_reimbursement": "Reimbursement",
        "current_budget": "Current Budget",
        "monthly_income": "Monthly Income",
        "potential_savings": "Potential Savings",
        "percent_budget_left": "% Budget Left",
        "percent_through_month": "% Through Month",
        "percent_budget_spent": "% Budget Spent",
        "home_balance": "House Savings",
        "miscellaneous_balance": "Misc Savings",
        "shared_balance": "Shared Savings",
        "planned_budget": "Planned Daily Budget",
        "adjusted_budget": "Adjusted Daily Budget",
        "date_updated": "Date Updated",
        "final_expense_record": "Last Expense"
    }

    REVERSE_DICT_TO_DASHBOARD: Dict[str, str] = {value: key for key, value in
                                                 DICT_TO_DASHBOARD.items()}

    DICT_TO_FORMAT: Dict[str, str] = {
        "amount_under_budget": "money",
        "checking_balance": "money",
        "amount_to_save": "money",
        "amount_budget_left": "money",
        "resulting_savings": "money",
        "monthly_expenses": "money",
        "monthly_savings": "money",
        "total_savings": "money",
        "net_worth": "money",
        "splitwise_balance": "money",
        "total_reimbursement": "money",
        "current_budget": "money",
        "monthly_income": "money",
        "potential_savings": "money",
        "percent_budget_left": "percent",
        "percent_through_month": "percent",
        "percent_budget_spent": "percent",
        "home_balance": "money",
        "miscellaneous_balance": "money",
        "shared_balance": "money",
        "planned_budget": "money",
        "adjusted_budget": "money",
        "date_updated": None,
        "final_expense_record": None
    }

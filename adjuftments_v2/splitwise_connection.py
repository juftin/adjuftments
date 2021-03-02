#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Splitwise Interactions
"""

import logging
from random import shuffle
from typing import List, Tuple, Union

from pandas import DataFrame
from splitwise import CurrentUser, Expense, Friend, SplitwiseException
from splitwise import Splitwise as SplitwiseConn
from splitwise.user import ExpenseUser

from adjuftments_v2.config import SplitwiseConfig
from adjuftments_v2.models import SplitwiseTable

logger = logging.getLogger(__name__)


class Splitwise(SplitwiseConn):
    """
    Python Class for interacting with Splitwise
    """
    __VERSION__ = 2.0

    def __init__(self, consumer_key: str, consumer_secret: str,
                 access_token: str, significant_other: str = None) -> None:
        """
        Splitwise

        Parameters
        ----------
        consumer_key: str
        consumer_secret: str
        access_token: str
        significant_other: str
        """
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.significant_other = significant_other

        super().__init__(
            consumer_key=consumer_key,
            consumer_secret=consumer_secret,
            access_token=access_token
        )

        current_user: CurrentUser = super().getCurrentUser()
        self.personal_id = current_user.id
        self.personal_email = current_user.email

    def __repr__(self):
        """
        String Representation

        Returns
        -------
        str
        """
        return f"<Splitwise: {self.personal_email}>"

    def _find_significant_other(self) -> Friend:
        """
        Get a Friend by Email

        Parameters
        ----------
        email: str

        Returns
        -------
        Friend
        """
        friend_list: List[Friend] = self.getFriends()
        for friend in friend_list:
            if friend.id == self.significant_other:
                return friend
        raise SplitwiseException(f"Friend not Found: {self.significant_other}")

    def get_balance(self) -> float:
        """
        Get Current balance

        Returns
        -------
        float
        """
        significant_other = self._find_significant_other()
        assert len(significant_other.balances) <= 1
        try:
            current_balance = significant_other.balances[0]
        except IndexError:
            return 0.00
        return float(current_balance.amount)

    def _get_transaction_balance(self, expense: Expense) -> float:
        """
        Retrieve a Transaction Balance

        Parameters
        ----------
        expense: Expense
            Splitwise Expense

        Returns
        -------
        float
        """
        # IF THERES ONLY 1 REPAYMENT AVAILABLE...
        if len(expense.repayments) == 1:
            repayment = expense.repayments[0]
            # IF TO JUSTIN/FROM SARAH:
            if repayment.toUser == self.personal_id and \
                    repayment.fromUser == self.significant_other and \
                    expense.payment is False:
                transaction_balance = float(expense.cost) - float(repayment.amount)
            # ELIF TO JUSTIN/FROM SARAH:
            elif repayment.fromUser == self.personal_id and \
                    repayment.toUser == self.significant_other and \
                    expense.payment is False:
                transaction_balance = float(repayment.amount)
            # OTHERWISE, DISCARD IT
            elif self.significant_other not in [user.id for user in expense.users]:
                logger.warning(f"Expense not between Significant Other: {expense.id}")
                return None
            elif expense.payment is True:
                transaction_balance = 0
        # IF THERE ARE NO REPAYMENTS
        elif len(expense.repayments) == 0:
            logger.critical(expense.__dict__)
            logger.critical(expense.users[0].first_name)
            assert len(expense.repayments) == 0
            assert expense.users[0].id == self.personal_id
            transaction_balance = -float(expense.cost)

        else:
            raise SplitwiseException(f"Cannot handle expense repayments: {expense.repayments}")

        return round(transaction_balance, 2)

    def process_expense(self, expense: Expense) -> dict:
        """
        Process an Expense object into a nice dictionary

        Parameters
        ----------
        expense: dict
            Splitwise Expense

        Returns
        -------
        dict
        """
        transaction_balance = self._get_transaction_balance(expense=expense)
        if transaction_balance is None:
            return None
        expense_dict = dict(id=expense.id,
                            transaction_balance=transaction_balance,
                            category=expense.category.name,
                            cost=round(float(expense.cost), 2),
                            created_at=expense.created_at,
                            created_by=expense.created_by.id,
                            currency=expense.currency_code,
                            date=expense.date,
                            deleted=True if expense.deleted_at is not None else False,
                            deleted_at=expense.deleted_at,
                            description=expense.description,
                            payment=expense.payment,
                            updated_at=expense.updated_at)
        return expense_dict

    def get_expenses(self, **kwargs) -> List[dict]:
        """
        Get Pertinent Expenses as JSON Dicts

        Parameters (Accepted KWARGS)
        ----------
        dated_after: datetime
            Return expenses later that this date
        dated_before: datetime
            Return expenses earlier than this date
        updated_after: datetime
            Return expenses updated after this date
        updated_before: datetime
            Return expenses updated before this date
        friendship_id: int
            FriendshipID of the expenses

        Returns
        -------
        expense_array: List[dict]
        """
        expense_array: List[dict] = list()
        if "limit" not in kwargs.keys():
            kwargs["limit"] = 0
        expense_object_list = self.getExpenses(**kwargs)
        for expense_object in expense_object_list:
            processed_dict = self.process_expense(expense=expense_object)
            if processed_dict is not None:
                expense_array.append(processed_dict)
            else:
                pass
        return expense_array

    @staticmethod
    def expenses_as_df(expense_array: List[dict]) -> DataFrame:
        """
        Return Expenses as Pandas Dataframe
        
        Parameters
        ----------
        expense_array

        Returns
        -------

        """
        expense_df = DataFrame(expense_array).astype(SplitwiseConfig.DTYPE_MAPPING)
        return expense_df

    @staticmethod
    def get_row(splitwise_record: dict) -> SplitwiseTable:
        """
        Insert a Row into the splitwise table

        Parameters
        ----------
        splitwise_record : dict
            Expense record for Splitwise

        Returns
        -------
        SplitwiseTable
        """
        new_splitwise_expense = SplitwiseTable(
            id=splitwise_record["id"],
            transaction_balance=splitwise_record["transaction_balance"],
            category=splitwise_record["category"],
            cost=splitwise_record["cost"],
            created_at=splitwise_record["created_at"],
            created_by=splitwise_record["created_by"],
            currency=splitwise_record["currency"],
            date=splitwise_record["date"],
            deleted=splitwise_record["deleted"],
            deleted_at=splitwise_record["deleted_at"],
            description=splitwise_record["description"],
            payment=splitwise_record["payment"],
            updated_at=splitwise_record["updated_at"])
        return new_splitwise_expense

    @staticmethod
    def split_a_transaction(amount: Union[float, int]) -> Tuple[float, float]:
        """
        Split a bill into a tuple of two amounts (and take care
        of the extra penny if needed)

        Parameters
        ----------
        amount: A Currency amount (no more precise than cents)

        Returns
        -------
        tuple
            A tuple is returned with each participant's amount
        """
        assert amount == round(amount, 2)
        first_owe = second_owe = (amount / 2)
        # IF EVEN DECIMALS
        if (amount * 100 % 2) == 0:
            amounts_due = (first_owe, second_owe)
        # OTHERWISE, RANDOMLY CHARGE A PENNY TO SOMEONE
        else:
            first_owe += 0.005
            second_owe -= 0.005
            # ROUNDING SEEMS REDUNDANT, BUT IT'S NOT... ¯\_(ツ)_/¯
            two_amounts = [round(first_owe, 2), round(second_owe, 2)]
            shuffle(two_amounts)
            amounts_due = tuple(two_amounts)
        return amounts_due

    def create_self_paid_expense(self, amount: float, description: str) -> Expense:
        """
        Create and Submit a Splitwise Expense

        Parameters
        ----------
        amount: float
            Transaction Amount
        description: str
            Transaction Description

        Returns
        -------
        Expense
        """
        # CREATE THE NEW EXPENSE OBJECT
        new_expense = Expense()
        # FORMAT THE DESCRIPTION
        parsed_description = description.split(" - ")
        if len(parsed_description) == 1:
            parsed_description = ["Splitwise"] + parsed_description
        parsed_description = [str(item).strip() for item in parsed_description]
        new_expense.setDescription(desc=" - ".join(parsed_description))
        # GET AND SET AMOUNTS OWED
        primary_user_owes, significant_other_owes = Splitwise.split_a_transaction(amount=amount)
        new_expense.setCost(cost=amount)
        # CONFIGURE PRIMARY USER
        primary_user = ExpenseUser()
        primary_user.setId(id=self.personal_id)
        primary_user.setPaidShare(paid_share=amount)
        primary_user.setOwedShare(owed_share=primary_user_owes)
        # CONFIGURE SECONDARY USER
        significant_other = ExpenseUser()
        significant_other.setId(id=self.significant_other)
        significant_other.setPaidShare(paid_share=0.00)
        significant_other.setOwedShare(owed_share=significant_other_owes)
        # ADD USERS AND REPAYMENTS TO EXPENSE
        new_expense.addUser(user=primary_user)
        new_expense.addUser(user=significant_other)
        # SUBMIT THE EXPENSE AND GET THE RESPONSE
        expense_response, expense_errors = self.createExpense(expense=new_expense)
        assert expense_errors is None
        return expense_response


if __name__ == "__main__":
    splitwiseObj = Splitwise(consumer_key=SplitwiseConfig.SPLITWISE_CONSUMER_KEY,
                             consumer_secret=SplitwiseConfig.SPLITWISE_CONSUMER_SECRET,
                             access_token=SplitwiseConfig.SPLITWISE_ACCESS_TOKEN,
                             significant_other=SplitwiseConfig.SPLITWISE_SIGNIFICANT_OTHER)
    expense_response = splitwiseObj.create_self_paid_expense(amount=13.00,
                                                             description="Testing for Adjuftments 2 ")
    print(expense_response.__dict__)
    expense_dict = splitwiseObj.process_expense(expense=expense_response)

#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

import logging
from typing import List

from pandas import DataFrame
from splitwise import CurrentUser, Expense, Friend, SplitwiseException
from splitwise import Splitwise as SplitwiseConn

from adjuftments_v2.config import SplitwiseConfig

logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s [%(levelname)8s]: %(message)s [%(name)s]",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO
                    )


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

    def find_friend(self) -> Friend:
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
        significant_other = self.find_friend()
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

        Returns
        -------

        """
        if len(expense.repayments) == 1:
            repayment = expense.repayments[0]
            if repayment.toUser == self.personal_id:
                transaction_balance = float(repayment.amount)
            elif repayment.toUser == self.significant_other:
                transaction_balance = -float(repayment.amount)
            elif self.significant_other not in [user.id for user in expense.users]:
                logger.debug(f"Expense not between Significant Other: {expense.id}")
                return None
        elif len(expense.repayments) == 0:
            assert len(expense.repayments) == 0
            assert expense.users[0].id == self.personal_id
            transaction_balance = -float(expense.cost)
        else:
            raise SplitwiseException(f"Cannot handle expense repayments: {expense.repayments}")
        return transaction_balance

    def _process_expense(self, expense: Expense):
        """
        Process an Expense object into a nice dictionary

        Parameters
        ----------
        expense

        Returns
        -------

        """
        transaction_balance = self._get_transaction_balance(expense=expense)
        if transaction_balance is None:
            return None
        expense_dict = dict(id=expense.id,
                            transaction_balance=transaction_balance,
                            category=expense.category.name,
                            cost=expense.cost,
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
        dated_after – ISO 8601 Date time. Return expenses later that this date
        dated_before – ISO 8601 Date time. Return expenses earlier than this date
        updated_after – ISO 8601 Date time. Return expenses updated after this date
        updated_before – ISO 8601 Date time. Return expenses updated before this date
        friendship_id – FriendshipID of the expenses

        Returns
        -------
        expense_array: List[dict]
        """
        expense_array: List[dict] = list()
        expense_object_list = self.getExpenses(limit=0,
                                               **kwargs)
        for expense_object in expense_object_list:
            processed_dict = self._process_expense(expense=expense_object)
            if processed_dict is not None:
                expense_array.append(processed_dict)
            else:
                pass
        return expense_array

    @staticmethod
    def expenses_as_df(expense_array: List[dict]) -> DataFrame:
        """

        Parameters
        ----------
        expense_array

        Returns
        -------

        """
        expense_df = DataFrame(expense_array).astype(SplitwiseConfig.DTYPE_MAPPING)
        return expense_df


if __name__ == "__main__":
    sw = Splitwise(consumer_key=SplitwiseConfig.SPLITWISE_CONSUMER_KEY,
                   consumer_secret=SplitwiseConfig.SPLITWISE_CONSUMER_SECRET,
                   access_token=SplitwiseConfig.SPLITWISE_ACCESS_TOKEN,
                   significant_other=SplitwiseConfig.SPLITWISE_SIGNIFICANT_OTHER)

    briz = sw.find_friend()
    flan = sw.getCurrentUser()
    cur_bal = sw.get_balance()
    expenses = sw.get_expenses()  # dated_after=datetime(year=2021, month=2, day=1))
    df = Splitwise.expenses_as_df(expenses)

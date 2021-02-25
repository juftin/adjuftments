#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

from datetime import datetime
import logging
from time import sleep
from warnings import filterwarnings

from sqlalchemy.exc import OperationalError

from adjuftments_v2 import Airtable, db, Splitwise
from adjuftments_v2.config import AirtableConfig, SplitwiseConfig
from adjuftments_v2.models import ExpensesTable, SplitwiseTable

filterwarnings("error")


def prepare_database():
    """
    Generate the Initial Database
    """
    from adjuftments_v2.models import ALL_TABLES
    logger.info(f"Preparing Database: {len(ALL_TABLES)} table(s)")

    wait_period = 5
    keep_trying = True
    while keep_trying:
        try:
            db.drop_all()
            db.create_all()
            logger.info("Database Created")
            keep_trying = False
        except OperationalError as oe:
            logger.error(oe)
            sleep(wait_period)


logging.basicConfig(format="%(asctime)s [%(levelname)8s]: %(message)s [%(name)s]",
                    handlers=[logging.StreamHandler()],
                    level=logging.INFO
                    )
logger = logging.getLogger(__name__)

prepare_database()
airtableExpenses = Airtable(base=AirtableConfig.AIRTABLE_BASE,
                            table="expenses")
splitwiseObj = Splitwise(consumer_key=SplitwiseConfig.SPLITWISE_CONSUMER_KEY,
                         consumer_secret=SplitwiseConfig.SPLITWISE_CONSUMER_SECRET,
                         access_token=SplitwiseConfig.SPLITWISE_ACCESS_TOKEN,
                         significant_other=SplitwiseConfig.SPLITWISE_SIGNIFICANT_OTHER)

logger.info(airtableExpenses)
logger.info(splitwiseObj)

airtable_records = airtableExpenses.get_all()
for airtable_record in airtable_records:
    new_db_expense = ExpensesTable(id=airtable_record["id"],
                                   amount=airtable_record["fields"].get("Amount"),
                                   category=airtable_record["fields"].get("Category"),
                                   date=airtable_record["fields"].get("Date"),
                                   imported=True,
                                   imported_at=str(datetime.utcnow()),
                                   transaction=airtable_record["fields"].get("Transaction"),
                                   uuid=airtable_record["fields"].get("UUID"),
                                   splitwise_id=airtable_record["fields"].get("splitwiseID"),
                                   )
    airtable_response = db.session.merge(new_db_expense)
    # airtableExpenses.update(record_id=response.id, fields=dict(ImportedAt=str(response.ImportedAt),
    #                                                            Imported=response.Imported),
    #                         typecast=True)
    db.session.commit()
    logger.info(
        f"Airtable Record Updated: {airtable_response.id} - {airtable_response.imported_at}")

splitwise_records = splitwiseObj.get_expenses()
for splitwise_record in splitwise_records:
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
    splitwise_response = db.session.merge(new_splitwise_expense)
    db.session.commit()
    logger.info(
        f"Splitwise Record Updated: {splitwise_response.id} - {splitwise_response.created_at}")

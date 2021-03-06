#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Adjuftments Plotting Utilities for Images
"""

from datetime import datetime
import logging
from time import sleep
from typing import Dict

from pandas import concat, DataFrame
import plotly.express as px
from plotly.graph_objs import Figure

from adjuftments import Adjuftments, Airtable, Dashboard
from adjuftments.config import AirtableConfig

logger = logging.getLogger(__name__)


class AdjuftmentsPlotting(object):
    """
    The Plotting Class
    """

    def __init__(self, adjuftments: Adjuftments):
        """
        Set the internal properties
        """
        _current_year = datetime.now().year
        self.historic_bases = AirtableConfig.HISTORIC_BASES.copy()
        self.historic_bases[str(_current_year)] = AirtableConfig.AIRTABLE_BASE
        self.adjuftments: Adjuftments = adjuftments

    def refresh_images(self) -> None:
        """
        Refresh Images within Airtable

        Returns
        -------
        None
        """
        image_dictionary = self._get_image_dictionary()
        self._publish_image_dictionary(image_dictionary=image_dictionary)

    # noinspection PyProtectedMember
    def _gather_historic_data(self) -> DataFrame:
        """
        Prepare a total historical dataframe

        Returns
        -------
        DataFrame
        """
        historic_dataframes = list()
        total_expenses_data = self.adjuftments._get_db_data(table="historic_expenses")
        expenses_df = Airtable.expenses_as_df(expense_array=total_expenses_data)
        for year, historic_base in sorted(self.historic_bases.items(), reverse=True):
            annual_expenses = expenses_df[expenses_df.date.dt.year == int(year)].copy()
            historic_account_data = self.adjuftments._get_airtable_data(
                table="accounts",
                params=dict(airtable_base=historic_base))
            balanced_data, account_balances = Dashboard._balance_df(
                expense_df=annual_expenses,
                bank_account_records=historic_account_data)
            logger.info(f"Ingesting {year} data, {len(annual_expenses)} records")
            historic_dataframes.append(balanced_data)
        return concat(historic_dataframes, ignore_index=True), account_balances

    @classmethod
    def _format_historical_data(cls, historical_data: DataFrame,
                                account_balances: dict) -> DataFrame:
        """
        Format the data and prepare for plotting

        Parameters
        ----------
        historical_data: DataFrame
            Compiled historical data

        Returns
        -------
        DataFrame
        """
        total_historic_data = historical_data.copy()
        balance_columns = total_historic_data.filter(regex="_balance").columns.tolist()
        total_historic_data["net_worth"] = total_historic_data[balance_columns].sum(axis=1)
        savings_columns = list()
        for account_name, account_data in account_balances["Savings"].items():
            savings_columns.append(account_data["column_name"])
        total_historic_data["total_savings"] = total_historic_data[savings_columns].sum(axis=1)
        graphing_columns = balance_columns + ["total_savings", "net_worth"]

        historical_rollup = total_historic_data.groupby(["date"])[
            graphing_columns].mean().reset_index(
            drop=False)
        historical_rollup[graphing_columns] = historical_rollup.rolling(7).mean()
        historical_rollup.rename(
            columns=lambda x: x.replace("_balance", "").replace("_", " ").title(),
            inplace=True)
        return historical_rollup

    @classmethod
    def _plot_account_balances(cls, historical_data: DataFrame) -> Figure:
        """
        Return a plot of all account balances

        Parameters
        ----------
        historical_data: DataFrame
            Compiled historical data

        Returns
        -------
        Figure
        """
        historical_columns = historical_data.columns.tolist()
        historical_columns.remove("Date")
        fig = px.line(data_frame=historical_data,
                      x="Date",
                      y=historical_columns,
                      title="Account Balances",
                      labels=dict(value="Amount ($)",
                                  variable="Account"),
                      render_mode="svg")
        fig.update_traces(line=dict(width=3))
        fig.update_layout(legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01
        ))
        return fig

    @classmethod
    def _plot_net_worth(cls, historical_data: DataFrame) -> Figure:
        """
        Return a plot of net worth

        Parameters
        ----------
        historical_data: DataFrame

        Returns
        -------
        Figure
        """
        fig = px.line(data_frame=historical_data,
                      x="Date",
                      y=["Net Worth"],
                      title="Net Worth",
                      labels=dict(value="Amount ($)"),
                      render_mode="svg")
        fig.update_traces(line=dict(width=4))
        fig.update_layout(showlegend=False)
        return fig

    def _get_image_dictionary(self) -> Dict[str, object]:
        """
        Gather an Image Dictionary to Parse

        Returns
        -------
        Dict[str, object]
        """
        historical_data, account_balances_dict = self._gather_historic_data()
        formatted_data = self._format_historical_data(historical_data=historical_data,
                                                      account_balances=account_balances_dict)
        account_balances = self._plot_account_balances(historical_data=formatted_data)
        personal_value = self._plot_net_worth(historical_data=formatted_data)
        image_dictionary = {'Account Balances': account_balances.to_image(scale=5),
                            'Personal Value': personal_value.to_image(scale=5)}
        return image_dictionary

    # noinspection PyProtectedMember
    def _publish_image_dictionary(self, image_dictionary: Dict[str, object]):
        """
        Publish an Image Dictionary to Airtable

        Returns
        -------
        Dict[str, object]
        """
        images_data = self.adjuftments._get_airtable_data(table="images")
        for image_record in images_data:
            image_payload = dict(image=image_dictionary[image_record["fields"]["Name"]])
            response = self.adjuftments.create_imgur_image(image_data=image_payload)
            image_url = response["data"]["link"]
            logger.info(f"Temporary Image Created: {image_url}")
            delete_hash = response["data"]["deletehash"]
            filename = image_record["fields"]["Name"].lower().replace(" ", "_") + ".png"
            image_update_dict = {"Attachment": [
                dict(url=image_url, filename=filename)]
            }
            self.adjuftments._update_airtable_record(table="images",
                                                     record_id=image_record["id"],
                                                     fields=image_update_dict)
            sleep(13)
            self.adjuftments.delete_imgur_image(delete_hash=delete_hash)

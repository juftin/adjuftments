#!/usr/bin/env python3

# Author::    Justin Flannery  (mailto:juftin@juftin.com)

"""
Adjuftments Plotting Utilities for Images
"""

from datetime import datetime
import logging
from os import getenv
from time import sleep
from typing import Dict

from pandas import concat, DataFrame
import plotly.express as px
from plotly.graph_objs import Figure

from adjuftments_v2 import Adjuftments, Airtable, Dashboard
from adjuftments_v2.config import AirtableConfig, FlaskDefaultConfig

logger = logging.getLogger(__name__)


class AdjuftmentsPlotting(object):
    """
    The Plotting Class
    """

    def __init__(self):
        """
        Set the internal properties
        """
        _current_year = datetime.now().year
        self.historic_bases = AirtableConfig.HISTORIC_BASES.copy()
        self.historic_bases[str(_current_year)] = AirtableConfig.AIRTABLE_BASE
        self.adjuftments = Adjuftments(endpoint=FlaskDefaultConfig.API_ENDPOINT,
                                       api_token=FlaskDefaultConfig.API_TOKEN)

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
        historic_expenses_data = self.adjuftments._get_db_data(table="historic_expenses")
        current_expenses_data = self.adjuftments._get_db_data(table="expenses")
        total_expenses_data = historic_expenses_data + current_expenses_data
        expenses_df = Airtable.expenses_as_df(expense_array=total_expenses_data)
        for year, historic_base in self.historic_bases.items():
            annual_expenses = expenses_df[expenses_df.date.dt.year == int(year)].copy()
            historic_misc_data = self.adjuftments._get_airtable_data(
                table="miscellaneous",
                params=dict(airtable_base=historic_base))
            miscellaneous_dict = self.adjuftments._get_miscellaneous_dict(
                miscellaneous_data=historic_misc_data)
            balanced_data = Dashboard._balance_df(
                dataframe=annual_expenses,
                starting_checking_balance=float(miscellaneous_dict["Starting Checking Balance"]),
                starting_miscellaneous_balance=float(
                    miscellaneous_dict["Starting Savings Balance"]),
                starting_home_balance=float(miscellaneous_dict["Starting House Balance"]),
                starting_shared_balance=float(miscellaneous_dict["Starting Shared Balance"])
            )
            logger.info(f"Ingesting {year} data, {len(annual_expenses)} records")
            historic_dataframes.append(balanced_data)
        return concat(historic_dataframes, ignore_index=True)

    @classmethod
    def _format_historical_data(cls, historical_data: DataFrame) -> DataFrame:
        """
        Format the data and prepare for plotting

        Parameters
        ----------
        historical_data: DataFrame

        Returns
        -------
        DataFrame
        """
        total_historic_data = historical_data.copy()
        desired_columns = ["checking_balance", "miscellaneous_balance",
                           "home_balance"]
        total_historic_data["savings_balance"] = total_historic_data["miscellaneous_balance"] + \
                                                 total_historic_data["home_balance"]
        total_historic_data["net_worth"] = total_historic_data["savings_balance"] + \
                                           total_historic_data["checking_balance"]
        desired_columns += ["savings_balance", "net_worth"]
        historical_rollup = total_historic_data.groupby(["date"])[
            desired_columns].mean().reset_index(drop=False)
        historical_rollup[desired_columns] = historical_rollup.rolling(7).mean()
        column_rename = dict(date="Date",
                             checking_balance="Checking",
                             miscellaneous_balance="Miscellaneous",
                             home_balance="Home",
                             savings_balance="Total Savings",
                             net_worth="Net Worth")
        historical_rollup.rename(columns=column_rename, inplace=True)
        return historical_rollup

    @classmethod
    def _plot_account_balances(cls, historical_data: DataFrame) -> Figure:
        """
        Return a plot of all account balances

        Parameters
        ----------
        historical_data: DataFrame

        Returns
        -------
        Figure
        """
        fig = px.line(data_frame=historical_data,
                      x="Date",
                      y=["Checking", "Miscellaneous", "Home", "Total Savings", "Net Worth"],
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
        historical_data = self._gather_historic_data()
        formatted_data = self._format_historical_data(historical_data=historical_data)
        account_balances = self._plot_account_balances(historical_data=formatted_data)
        personal_value = self._plot_net_worth(historical_data=formatted_data)
        image_dictionary = {'Account Balances': account_balances.to_image(scale=5),
                            'Personal Value': personal_value.to_image(scale=5)}
        return image_dictionary

    # noinspection PyProtectedMember
    def _publish_image_dictionary(self, image_dictionary: Dict[str, object]):
        """
        Pulish an Image Dictionary to Airtable

        Returns
        -------
        Dict[str, object]
        """
        images_data = self.adjuftments._get_airtable_data(table="images")
        for image_record in images_data:
            image_payload = dict(image=image_dictionary[image_record["fields"]["Name"]])
            response = self.adjuftments._create_imgur_image(image_data=image_payload)
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
            self.adjuftments._delete_imgur_image(delete_hash=delete_hash)

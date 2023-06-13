import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from lxml import html
import requests
from collections import OrderedDict
import json

# RUN THIS THE START OF EVERY MONTH TO UPDATE MONTHLY PRODUCTION TO INCLUDE THE PREVIOUS MONTH
def main():
    updateMonthlyData()
    updateCumMoData()


def updateMonthlyData():
    df_daily = pd.read_csv('data.csv')
    df_daily['Date'] = pd.to_datetime(df_daily['Date'])
    df_daily['Month'] = df_daily['Date'].dt.month
    df_daily['Year'] = df_daily['Date'].dt.year

    grouped = df_daily.groupby(['Well Name', 'Year', 'Month'])
    monthly_sum = grouped.sum().reset_index()

    monthly_sum['Date'] = pd.to_datetime(monthly_sum[['Year', 'Month']].assign(day=1))
    monthly_sum = monthly_sum.drop('Year', axis=1)
    monthly_sum = monthly_sum.drop('Month', axis=1)

    monthly_sum.to_csv("monthlyDataST.csv", index=False)

    # FILE DESTINATION, CHANGE TO FIT YOUR LOCAL GITHUB FOLDER. File name: "dataMonthlyST.json"
    monthly_sum.to_json("../prod-1/data/dataMonthlyST.json", orient='values', date_format='iso')
    #------------------^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^-----------------------------------------#


def updateCumMoData():
    df_daily = pd.read_csv('data.csv')
    df_daily['Date'] = pd.to_datetime(df_daily['Date'])
    df_daily['Month'] = df_daily['Date'].dt.month
    df_daily['Year'] = df_daily['Date'].dt.year

    grouped = df_daily.groupby(['Well Name', 'Year', 'Month'])
    monthly_sum = grouped.sum().reset_index()

    # Calculate the cumulative sum on selected columns
    group = monthly_sum.groupby('Well Name')
    final_cumsum = group['Oil (BBLS)', 'Gas (MCF)', 'Water (BBLS)'].cumsum()
    monthly_sum[['Oil (BBLS)', 'Gas (MCF)', 'Water (BBLS)']] = final_cumsum

    # Date column, drop year & month columns
    monthly_sum['Date'] = pd.to_datetime(monthly_sum[['Year', 'Month']].assign(day=1))
    monthly_sum = monthly_sum.drop('Year', axis=1)
    monthly_sum = monthly_sum.drop('Month', axis=1)

    monthly_sum.to_csv("monthlyCumDataST.csv", index=False)

    # FILE DESTINATION, CHANGE TO FIT YOUR LOCAL GITHUB FOLDER. File name: "cumDataMonthlyST.json"
    monthly_sum.to_json("../prod-1/data/cumDataMonthlyST.json", orient='values', date_format='iso')
    #------------------^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^-----------------------------------------#


main()
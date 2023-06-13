import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from lxml import html
import requests
from collections import OrderedDict
import json

# Run this the start of every month to update monthly production from the last month
def main():
    createMdataByNameJson()


def createMdataByNameJson():
    df_daily = pd.read_csv('data.csv')
    df_daily['Date'] = pd.to_datetime(df_daily['Date'])
    df_daily['Month'] = df_daily['Date'].dt.month
    df_daily['Year'] = df_daily['Date'].dt.year

    grouped = df_daily.groupby(['Well Name', 'Year', 'Month'])
    monthly_sum = grouped.sum().reset_index()

    monthly_sum['Date'] = pd.to_datetime(monthly_sum[['Year', 'Month']].assign(day=1))
    monthly_sum = monthly_sum.drop('Year', axis=1)
    monthly_sum = monthly_sum.drop('Month', axis=1)

    monthly_sum.to_csv("monthlySumData.csv", index=False)

    # FILE DESTINATION, CHANGE TO FIT YOUR LOCAL GITHUB FOLDER. File name: "sumDataMonthly.json"
    monthly_sum.to_json("../prod-1/data/sumDataMonthly.json", orient='values', date_format='iso')
    #------------------^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^-----------------------------------------#

    exit()

main()

# Unused
def createMdataCSV():
    df_daily = pd.read_csv('data.csv')
    df_daily['Date'] = pd.to_datetime(df_daily['Date'])
    df_daily['Month'] = df_daily['Date'].dt.month
    df_daily['Year'] = df_daily['Date'].dt.year

    grouped = df_daily.groupby(['Year', 'Month'])
    monthly_sum = grouped.sum()

    monthly_sum.to_csv('Mdata.csv')
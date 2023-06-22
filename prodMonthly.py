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
    updateWellList()

def updateMonthlyData():
    # Read ST daily data file, group by Well Name, Year, and Month
    df_daily = pd.read_csv('data.csv')
    df_daily['Date'] = pd.to_datetime(df_daily['Date'])
    df_daily['Month'] = df_daily['Date'].dt.month
    df_daily['Year'] = df_daily['Date'].dt.year
    grouped = df_daily.groupby(['Well Name', 'Year', 'Month'])
    
    # Sum all groups (sum up production from each month), format date column & drop other columns
    monthly_sum = grouped.sum().reset_index()
    monthly_sum['Date'] = pd.to_datetime(monthly_sum[['Year', 'Month']].assign(day=1))
    monthly_sum = monthly_sum.drop('Year', axis=1)
    monthly_sum = monthly_sum.drop('Month', axis=1)

    monthly_sum = monthly_sum.sort_values('Date').reset_index(drop=True)

    monthly_sum.to_csv("monthlyDataST.csv", index=False)

    # FILE DESTINATION, CHANGE TO FIT YOUR LOCAL GITHUB FOLDER. File name: "dataMonthlyST.json"
    monthly_sum.to_json("../prod/data/dataMonthlyST.json", orient='values', date_format='iso')
    #------------------^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^-----------------------------------------#

main()


# NO LONGER IN USE
def updateCumMoData():
    # Sum production data by month
    df_daily = pd.read_csv('data.csv')
    df_daily['Date'] = pd.to_datetime(df_daily['Date'])
    df_daily['Month'] = df_daily['Date'].dt.month
    df_daily['Year'] = df_daily['Date'].dt.year
    grouped = df_daily.groupby(['Well Name', 'Year', 'Month'])
    monthly_sum = grouped.sum().reset_index()

    # Calculate the cumulative sum for each well, up to date
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

# RETURNS LIST OF ALL EXISTING WELLS (FROM monthlyDataST.csv)
def updateWellList():
    df = pd.read_csv('monthlyDataST.csv')
    wells = df["Well Name"].to_list()
    wells = set(wells)
    wells = list(wells)

    # Open the file in write mode
    with open('everyWell.json', 'w') as json_file:
        # Use the json.dump() function to write the list to the file
        json.dump(wells, json_file)

    with open('../prod/data/declineCurves/1wells.json', 'w') as json_file:
        # Use the json.dump() function to write the list to the file
        json.dump(wells, json_file)
    

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from lxml import html
import requests
from collections import OrderedDict
import json

# NOT IN USE, REPLACED BY FUNTION IN FRONTEND THAT CUMULATIVELY SUMS

# def main():
#     updateCumDailyData()

# def updateCumDailyData():
#     df_daily = pd.read_csv('data.csv', usecols=['Well Name', 'Oil (BBLS)', 'Date'])

#     # Convert the datetime column to datetime format if needed
#     df_sorted = df_daily.sort_values(['Well Name', 'Date']).reset_index(drop=True)

#     group = df_sorted.groupby('Well Name')
#     final_cumsum = group['Oil (BBLS)'].cumsum()
#     df_sorted['Cum Oil (BBLS)'] = final_cumsum

#     df_sorted.to_csv('test.csv', index=False)

#     # FILE DESTINATION, CHANGE TO FIT YOUR LOCAL GITHUB FOLDER. File name: "cumDataMonthlyST.json"
#     df_sorted.to_json("../prod-1/data/cumDataDailyST.json", orient='values', date_format='iso')
#     #----------------^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^---------------------------------------#

#     exit()

# main()
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from datetime import datetime, timedelta
from itertools import zip_longest
from dateutil.relativedelta import relativedelta

def main():
    updateStartDate()

# Creates file that has all start dates for wells
def updateStartDate():
    # Read ST daily data file, group by Well Name
    df_daily = pd.read_csv('data.csv')
    df_daily['Date'] = pd.to_datetime(df_daily['Date'])
    # After grouping, get last index, reset grouping, drop unneeded columns
    last_entries = df_daily.groupby('Well Name').last().drop(['Oil (BBLS)','Gas (MCF)','Water (BBLS)','TP','CP','Comments'], axis=1)

    # FILE DESTINATION, CHANGE TO FIT YOUR LOCAL GITHUB FOLDER. File name: "dataMonthlyST.json"
    last_entries.to_json("../prod/data/wellStartDates.json", date_format='iso')
    #---------------------^^^^^^^^^^^^^-------------------------------------------------------#

main()

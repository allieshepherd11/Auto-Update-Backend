import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from datetime import date, datetime, timedelta
from itertools import zip_longest
from dateutil.relativedelta import relativedelta

def main():
    # updateStartDate()
    startInLastYearProduction()

# Creates file that has all start dates for wells
def updateStartDate():
    # Read ST daily data file, group by Well Name
    df_daily = pd.read_csv('data.csv')
    df_daily['Date'] = pd.to_datetime(df_daily['Date'])
    # After grouping, get last index, reset grouping, drop unneeded columns
    last_entries = df_daily.groupby('Well Name').last().reset_index().drop(['Oil (BBLS)','Gas (MCF)','Water (BBLS)','TP','CP','Comments'], axis=1)
    last_entries.to_csv('wellStartDates.csv', index=False)

    # last_entries = df_daily.groupby('Well Name').last().drop(['Oil (BBLS)','Gas (MCF)','Water (BBLS)','TP','CP','Comments'], axis=1)
    # FILE DESTINATION, CHANGE TO FIT YOUR LOCAL GITHUB FOLDER. File name: "dataMonthlyST.json"
    # last_entries.to_json("../prod/data/wellStartDates.json", date_format='iso')
    #---------------------^^^^^^^^^^^^^-------------------------------------------------------#

def startInLastYearProduction():
#   // Filter the start dates for... the past year
    df_start_dates = pd.read_csv('wellStartDates.csv')
    current_date = datetime.today()
    year_prior = (current_date - timedelta(days=365)).strftime("%Y-%m-%d")
    year_prior = datetime.strptime(year_prior, "%Y-%m-%d")
    
    well_list = pd.DataFrame(columns=['Well Name', 'Date'])
    for index, row in df_start_dates.iterrows():
        t_date = datetime.strptime(row['Date'], "%Y-%m-%d")
        if(year_prior <= t_date <= current_date):
            well_list = well_list.append(row, ignore_index=True)
    print(well_list)

    # print(well_list)

#   // Filter the daily prod data by well names
    df_dp = pd.read_csv('data.csv')
    df_dp = df_dp.drop(['Gas (MCF)','Water (BBLS)','TP','CP','Comments'], axis=1)
    # filtname_df = df_dp[df_dp['Well Name'].isin(well_list['Well Name'])]

    df_dp['Date'] = pd.to_datetime(df_dp['Date'])
    f_df = df_dp[(df_dp['Well Name'].isin(well_list['Well Name'])) & (df_dp['Date'] >= year_prior) & (df_dp['Date'] <= current_date)]

    f_df.to_csv('wtest.csv')




    # f_df['Date'] = pd.to_datetime(f_df['Date'])
    f_df['Month'] = f_df['Date'].dt.month
    f_df['Year'] = f_df['Date'].dt.year
    grouped = f_df.groupby(['Year', 'Month'])
    
    # Sum all groups (sum up production from each month), format date column & drop other columns
    monthly_sum = grouped.sum().reset_index()
    monthly_sum['Date'] = pd.to_datetime(monthly_sum[['Year', 'Month']].assign(day=1))
    print(monthly_sum)

    # What this is doing: Sum up all months with the same values
    # What we actually want to do: Sum up the production for the day, only including values from wells that started one year ago
        
    
    # & (df_dp['Date'] >= year_prior) & (df_dp['Date'] <= current_date)]





#   // Filter the daily prod data by the last 365 days

#   // sum the wells' data by each day

#   // Graph the arrays

main()

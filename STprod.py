import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from lxml import html
import requests
from collections import OrderedDict
import json

def main():
    dtype = {'Oil (BBLS)': float, 'Water (BBLS)': float, 'Gas (MCF)': float, 'TP': float, 'CP': float, 'Comments': str}
    df = pd.read_csv('data.csv', dtype=dtype)
    # df = pd.read_json('data.json')
    df = df.fillna('')
    df.Date = pd.to_datetime(df.Date)
    df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])

    # Get list of days that need production imported. Prevents the need for manual input
    end = datetime.today().date() # Gets today's date
    start = df.iloc[0]['Date'].date() # Gets the most recent date from the dataframe
    numdays = (end-start).days # Calculates the number of days between the above two dates
    date_list = [end - timedelta(days=x) for x in range(numdays)]

    #  Loop through dates that need production imported and try the different file name possibilities based on when the server sends the emails
    for i in range(numdays-1):
        try:
            importFile = 'custom-report-cml_' + str(date_list[i]) + '_8-00-03.csv'
            dfImport = pd.read_csv(importFile, dtype = dtype, thousands=',')
        except:
            try:
                importFile = 'custom-report-cml_' + str(date_list[i]) + '_8-00-04.csv'
                dfImport = pd.read_csv(importFile, dtype = dtype, thousands=',')
            except:
                try:
                    importFile = 'custom-report-cml_' + str(date_list[i]) + '_8-00-02.csv'
                    dfImport = pd.read_csv(importFile, dtype = dtype, thousands=',')
                except:
                    print('The file for this date does not exist')
        dfImport = dfImport.fillna('')
        dfImport.Date = pd.to_datetime(dfImport.Date)
        df = pd.concat([df,dfImport]).drop_duplicates()
        
    df['Gas (MCF)'] = pd.to_numeric(df['Gas (MCF)'])
    df.reset_index(drop=True, inplace=True) # Does this do anything?

    # Fix blanks and clip negative values
    df['Oil (BBLS)'].replace('',0, inplace=True)
    df['Water (BBLS)'].replace('',0, inplace=True)
    df['Gas (MCF)'].replace('',0, inplace=True)
    df['Oil (BBLS)'] = df['Oil (BBLS)'].round()
    df['Water (BBLS)'] = df['Water (BBLS)'].clip(lower=0).round()
    df['Gas (MCF)'] = df['Gas (MCF)'].clip(lower=0).round()
    df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])

    # Don't run until we have website running for all fields
    # print(days_since_last_production(df))

    # Save to original data file
    # df.to_json('data.json')
    df.to_csv('data.csv', index=False)

    # Get 30 day moving average and append column to df
    df = df.sort_values(['Date', 'Well Name'], ascending = [True , True])
    df['7DMA'] = df.groupby('Well Name')['Oil (BBLS)'].transform(lambda x: x.rolling(7, 1).mean().round(1))
    df['30DMA'] = df.groupby('Well Name')['Oil (BBLS)'].transform(lambda x: x.rolling(30, 1).mean().round(1))
    df['MA Ratio'] = df['7DMA']/df['30DMA']
    df['MA Ratio'] = df['MA Ratio'].round(2)
    df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])
    analyze(df)
    df.drop(['30DMA', 'MA Ratio'], inplace=True, axis = 1)

    ############################################################################################################################################
    # Code below is for miscellaneous tasks that rarely need to be performed

    # Code to replace incorrect values. Will need to be run on Pickens once per week
    # df.loc[(df['Well Name'] == 'Pickens #1') & (df['TP'] == 200), ['Oil (BBLS)', 'Gas (MCF)', 'Water (BBLS)', 'TP']] = [0.0, 0.0, 0.0, 100.0]
    # df.loc[(df['Well Name'] == 'Pickens #1')].head(60)
    # df.loc[df['Well Name'].isin(['Dunlap #1', 'Dunkle #2'])]



    # SET OIL ON A CERTAIN DATE TO A NEW VALUE
    # df.loc[(df['Well Name'] == 'Pecan Grove #1') & (df['Date'] == '2021-03-15'), 'Oil (BBLS)'] = 0.0

    # df.to_json('data.json')

    # GOR
    # gas_col = df_query['Gas (MCF)']
    # oil_col = df_query['Oil (BBLS)']

    # df_query['GOR'] = gas_col/oil_col.replace(0,np.nan)*1000
    # df_query['GOR'] = df_query['GOR'].astype(float)
    # df_query['GOR'] = df_query['GOR'].round(decimals = 0)

    # df_query.head()



    # # Create dataframes for different time periods
    # df7day = df[(df['Date'] > datetime.now() - pd.to_timedelta('8day'))]

    # # df30day = df[(df['Date'] > datetime.now() - pd.to_timedelta('31day'))]
    # # df30day

    # df365day = df[(df['Date'] > datetime.now() - pd.to_timedelta('366day'))]


    # # Get mean of yearly and weekly prod
    # yearlyavg = df365day.groupby('Well Name', as_index = False).agg({'Oil (BBLS)': ['mean']})
    # yearlyavg.columns = ['Well Name', '365 Day Avg Oil']

    # weeklyavg = df7day.groupby('Well Name', as_index = False).agg({'Oil (BBLS)': ['mean']})
    # weeklyavg.columns = ['Well Name', '7 Day Avg Oil']

    # # Merge dataframes
    # dfprod = weeklyavg.merge(yearlyavg, how='left', on='Well Name')
    # dfprod['Difference'] = dfprod.apply(lambda row: row['7 Day Avg Oil'] - row['365 Day Avg Oil'], axis = 1)
    ############################################################################################################################################

    dfoil = df.groupby(['Well Name'])['Oil (BBLS)'].sum().divide(1000).astype(float).reset_index().round(1)
    dfwater = df.groupby(['Well Name'])['Water (BBLS)'].sum().divide(1000).astype(float).reset_index().round(1)
    dfgas = df.groupby(['Well Name'])['Gas (MCF)'].sum().divide(1000).astype(int).reset_index()
    df_formations = get_formations()

    dfsum = dfoil.merge(dfwater, on='Well Name').merge(dfgas, on='Well Name').merge(df_formations, on='Well Name')

    # Create entries for total field production in a way that can integrate with graph
    dfoiltotal = df.groupby(['Date'])['Oil (BBLS)'].sum().astype(int).reset_index()
    dfwatertotal = df.groupby(['Date'])['Water (BBLS)'].sum().astype(int).reset_index()
    dfgastotal = df.groupby(['Date'])['Gas (MCF)'].sum().astype(int).reset_index()

    dfsummary = dfoiltotal.merge(dfwatertotal, on='Date').merge(dfgastotal, on='Date')

    dfsummary['Well Name'] = 'South Texas Total'
    dfwebsite = pd.concat([df, dfsummary])
    dfwebsite = dfwebsite.sort_values(['Date', 'Well Name'], ascending = [False , True])

    # CREATING A DF SPECIFIC TO JSON FORMAT (DATETIME)
    df_to_json_format = dfwebsite

    # ADD DATE COLUMN FOR X AXIS USE (DateYAxis) & CHANGING DATATYPE TO Object
    df_to_json_format['DateYAxis'] =  df_to_json_format['Date']
    df_to_json_format['DateYAxis'] =  pd.to_datetime(df_to_json_format['Date'])

    # CHANGING DATE TO OBJECT TYPE AND SPELL OUT FORMAT
    df_to_json_format['Date'] =  pd.to_datetime(df_to_json_format['Date'])
    # df_to_json_format['Date'] = df_to_json_format['Date'].dt.strftime('%Y-%m-%d')
    df_to_json_format['Date'] = df_to_json_format['Date'].dt.strftime('%B %d, %Y')


    # SAVING ALL PRODUCTION DATA TO WEBSITE FOLDER
    df_to_json_format.to_json("../STprodWebsite/STprod/static/allProductionData.json", orient='values', date_format='iso')

    # SAVING ALL PRODUCTION DATA TO WEBSITE FOLDER
    dfsum.to_json("../STprodWebsite/STprod/static/cumProd.json", orient='values')
    
    pump_info()
    # scrape_oil_price()
    # scrape_gas_price()


### Functions ###

# Days from last production
def days_since_last_production(df):
    wells = df['Well Name'].unique()
    days_since_production = []

    for well in wells:
        well_data = df[df['Well Name'] == well]
        last_production_date = None

        for index, row in well_data.iterrows():
            if row['Oil (BBLS)'] > 0 or row['Gas (MCF)'] > 0:
                last_production_date = row['Date']
                break

        if last_production_date is not None:
            days_since = (datetime.today().date() - last_production_date.date()).days
        else:
            days_since = np.nan

        days_since_production.append((well, days_since))

    return pd.DataFrame(days_since_production, columns=['Well Name', 'Days since last Production'])

# Save pump parameters
def pump_info():
    df_info = pd.read_excel('../CML/STprod.xlsx', sheet_name = 'Prod', usecols= 'A,I:R')
    # df_info.to_csv('example.csv', index= False)
    df_info.to_json("../STprodWebsite/STprod/static/pumpInfo.json", orient='records')

def get_formations():
    df_formations = pd.read_excel('formations.xlsx')
    return df_formations
    # df_formations.to_json("C:/Users/wadmant/Desktop/OneDrive - CML Exploration/STprodWebsite/STprod/static/formations.json", orient='records')

# Return and save list of wells that are performing poorly on the
def analyze(df):
    df_analysis = df[
        (df['Date'] == df['Date'].max()) & (~df['Comments'].str.contains('off', case=False)) & (df['30DMA'] > 4) &
        (
            ((df['MA Ratio'] < 0.8) & (df['Oil (BBLS)'] < df['30DMA'] * 0.8)) |
            (df['Oil (BBLS)'] == 0)
        )
    ]
    df_analysis['Date'] = df_analysis['Date'].dt.strftime('%B %d, %Y')
    df_analysis.to_json("../STprodWebsite/STprod/static/analyze.json", orient='records')
    
def oil_revenue(price, bopd):
    return round(price*.75*.954*bopd,2)

def scrape_oil_price():
    url = 'https://finance.yahoo.com/quote/CL=F?p=CL%3DF'

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Pragma': 'no-cache',
        'Referrer': 'https://google.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36'
    }

    page = requests.get(url, headers)
    tree = html.fromstring(page.content)

    summary_table = tree.xpath(
    '//div[contains(@data-test,"summary-table")]//tr')

    summary_data = OrderedDict()
    for table_data in summary_table:
            raw_table_key = table_data.xpath('.//td[1]//text()')
            raw_table_value = table_data.xpath('.//td[2]//text()')
            table_key = ''.join(raw_table_key).strip()
            table_value = ''.join(raw_table_value).strip()
            summary_data.update({table_key: table_value})

    with open('C:/Users/wadmant/Desktop/OneDrive - CML Exploration/STprodWebsite/STprod/static/oilprice.json', 'w') as fp:
        json.dump(summary_data, fp, indent=4)

def scrape_gas_price():
    url = 'https://finance.yahoo.com/quote/NG=F?p=NG=F&.tsrc=fin-srch'

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Pragma': 'no-cache',
        'Referrer': 'https://google.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36'
    }

    page = requests.get(url, headers)
    tree = html.fromstring(page.content)

    summary_table = tree.xpath(
    '//div[contains(@data-test,"summary-table")]//tr')

    summary_data = OrderedDict()
    for table_data in summary_table:
            raw_table_key = table_data.xpath('.//td[1]//text()')
            raw_table_value = table_data.xpath('.//td[2]//text()')
            table_key = ''.join(raw_table_key).strip()
            table_value = ''.join(raw_table_value).strip()
            summary_data.update({table_key: table_value})

    with open('../STprodWebsite/STprod/static/gasprice.json', 'w') as fp:
        json.dump(summary_data, fp, indent=4)

# Execute program
if __name__ == '__main__':
    main()
import pandas as pd
from datetime import datetime, timedelta
from lxml import html
import requests
from collections import OrderedDict
import json
import time
import os 
import boto3
from dotenv import load_dotenv
import time


def main():
    dtype = {'Oil (BBLS)': float, 'Water (BBLS)': float, 'Gas (MCF)': float, 'TP': str, 'CP': str, 'Comments': str}
    df = pd.read_csv('db\prod\data.csv', dtype=dtype)
    #df = pd.read_json('data.json')
    df = df.fillna('')
    df.Date = pd.to_datetime(df.Date)
    df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])
    start = df.iloc[0]['Date'].date() # Gets the most recent date from the dataframe

    # Import recent data from email 
    #dfImport = importDataEmail(start,dtype)
    current_datetime = time.time()
    # Import recent data from iwell
    dfImport,updates = importDataIwell(start)
    print("time: ", time.time() - current_datetime)
    print(dfImport)
    print(updates)
    # Update df 
    if updates:
        for i in updates:
            df.loc[(df['Well Name'] == i["Well Name"]) & (df['Date'] == i["date"]), 'Oil (BBLS)'] = i["oil"]
            df.loc[(df['Well Name'] == i["Well Name"]) & (df['Date'] == i["date"]), 'Gas (MCF)'] = i["gas"]
            df.loc[(df['Well Name'] == i["Well Name"]) & (df['Date'] == i["date"]), 'Water (BBLS)'] = i["water"]
        

    df = pd.concat([df,dfImport]).drop_duplicates()
    print("\ndf:\n",df)
    df['Gas (MCF)'] = pd.to_numeric(df['Gas (MCF)'])
    df.reset_index(drop=True, inplace=True)

    # Fix blanks and clip negative values
    df['Oil (BBLS)'].replace('',0, inplace=True)
    df['Water (BBLS)'].replace('',0, inplace=True)
    df['Gas (MCF)'].replace('',0, inplace=True)
    df['Oil (BBLS)'] = df['Oil (BBLS)'].clip(lower=0).round()
    df['Water (BBLS)'] = df['Water (BBLS)'].clip(lower=0).round()
    df['Gas (MCF)'] = df['Gas (MCF)'].clip(lower=0).round()
    df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])
    
    #Add total fluid column
    #df['Total Fluid'] = df['Oil (BBLS)'] + df['Water (BBLS)']

    # Save to original data file
    df.to_json('data1.json')
    df.to_csv('data1.csv', index=False)

    # Get 30 day moving average and append column to df
    df = df.sort_values(['Date', 'Well Name'], ascending = [True , True])
    df['7DMA'] = df.groupby('Well Name')['Oil (BBLS)'].transform(lambda x: x.rolling(7, 1).mean().round(1))
    df['30DMA'] = df.groupby('Well Name')['Oil (BBLS)'].transform(lambda x: x.rolling(30, 1).mean().round(1))
    df['MA Ratio'] = df['7DMA']/df['30DMA']
    df['MA Ratio'] = df['MA Ratio'].round(2)
    df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])
    ##analyze(df)
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

    #CHANGING DATE TO OBJECT TYPE AND SPELL OUT FORMAT
    df_to_json_format['Date'] =  pd.to_datetime(df_to_json_format['Date'])
    #df_to_json_format['Date'] = df_to_json_format['Date'].dt.strftime('%Y-%m-%d')
    df_to_json_format['Date'] = df_to_json_format['Date'].dt.strftime('%B %d, %Y')
    
    #add new total fluid col, needs to last col in df to mess up js for website, or add after gas col and change graph.js to point to new indexes 
    dfwebsite['Total Fluid'] = df['Oil (BBLS)'] + df['Water (BBLS)']
    
    

    # SAVING ALL PRODUCTION DATA TO WEBSITE FOLDER
    ##df_to_json_format.to_json("../STprodWebsite/STprod/static/allProductionData.json", orient='values', date_format='iso')
    
    # SAVING ALL PRODUCTION DATA TO WEBSITE FOLDER
    #dfsum.to_json("../STprodWebsite/STprod/static/cumProd.json", orient='values')
    
    #df_info = pd.read_excel('../CML/STprod.xlsx', sheet_name = 'Prod', usecols= 'A,I:R')
    # SAVE & UPLOAD TO AWS WEBSITE
    df_to_json_format.to_json("update/allProductionData.json", orient='values', date_format='iso') #updating loc json file
    dfsum.to_json("update/cumProd.json", orient='values', date_format='iso')
    df_formations.to_json("formations.json", orient='values', date_format='iso')
    #df_info.to_json("pumpinfo.json", orient='values', date_format='iso')

    exportf = "allProductionData.json" #file in loc folder
    file_to_update = "static/allProductionData.json" #path to file in aws bucket

    #updateAwsSite(exportf,file_to_update)
    #updateAwsSite("cumProd.json","static/cumProd.json")
    #updateAwsSite("formations.json","static/formations.json")
    #updateAwsSite("pumpinfo.json","static/pumpInfo.json")

    #pump_info()
    #get_formations()

## iwell Api init ##
load_dotenv()
client_id = os.getenv('client_id')
client_secret = os.getenv('client_secret')
username = os.getenv('email')
password = os.getenv('password')

### Functions ###

def importDataIwell(start):
    importData = []
    #unix_time_since = 1657515600#july 11 0:00

    
    unix_time_since = time.mktime(datetime.strptime(str(start), "%Y-%m-%d").timetuple()) #unix time since last import, most recent date is removed in line 52/53. max is 30 days ago
    if (datetime.today().date()-start).days > 30:
        print("too far in past")
        exit()
    token = init()
    me(token)
    wellGroup = well_group(token)
    
    st = single_well_group(token, wellGroup['SOUTH TEXAS'])#All ST wells
    print(len(st))
    
    wells = list(st.keys())
    for well in wells:
        if 'Drip' in well or 'Compressor' in well:
            del st[well]
    
    updates = []
    for well in sorted(st):
        try:
            prod = well_production(token,st[well],unix_time_since)
            tp = well_field_value(token,st[well],607,unix_time_since)
            cp = well_field_value(token,st[well],1415,unix_time_since)
            comm = well_comments(token,st[well],unix_time_since)
            print(well)
        except Exception as e:
            print(e,"no data for",well)
            if len(prod[1]) % 5 == 0:
                print("sleeping...")
                time.sleep(61)
            continue
        #print("len:",len(prod[1]), prod[2])
        if len(prod[1]) % 5 == 0:
            print("sleeping...")
            time.sleep(61)

        for i in prod[0][:]:
            if i["production_time"] != i["updated_at"] and i["production_time"] < unix_time_since and i["date"] != str(datetime.today().date()):#gets updated prod, but not today or updates since last import
                i["Well Name"] = well
                updates.append(i)
                prod[0].remove(i)

        for i in prod[0][:]:# copy of list
            if i["date"] == str(datetime.today().date()) or i["date"] == str(start) or time.mktime(datetime.strptime(i["date"], "%Y-%m-%d").timetuple()) < unix_time_since:
                prod[0].remove(i)
        
        #get list of production time for cp and tp
        cp_times = []
        tp_times = []
        for i in range(len(cp)):
            cp_times.append(cp[i]["updated_at"])
        for i in range(len(tp)):
            tp_times.append(tp[i]["updated_at"])
        
        for i in range(len(prod[0])):
            date = prod[0][i]["date"]
            date_2300 = time.mktime(datetime.strptime(date, "%Y-%m-%d").timetuple()) + 82800#11pm on day of production
            
            #use tp/cp value that is recorded at the end of day
            try:
                most_recent_cp = min(cp_times, key=lambda x:abs(x-date_2300))
                for j in cp:
                    if j["updated_at"] == most_recent_cp:
                        cp_value = j["value"]
                        break
            except:#no cp data
                cp_value = ""
            try:
                most_recent_tp = min(tp_times, key=lambda x:abs(x-date_2300))
                for k in tp:
                    if k["updated_at"] == most_recent_tp:
                        tp_value = k["value"]
                        break
            except:#no tp data
                tp_value = ""
            try:
                importData.append([well,prod[0][i]["date"],prod[0][i]["oil"],prod[0][i]["gas"],prod[0][i]["water"],tp_value,cp_value,comm[i]])
            except:#no comment
                importData.append([well,prod[0][i]["date"],prod[0][i]["oil"],prod[0][i]["gas"],prod[0][i]["water"],tp_value,cp_value,""])

        
    

    dfimport = pd.DataFrame(data=importData,columns=["Well Name","Date","Oil (BBLS)","Gas (MCF)","Water (BBLS)","TP","CP","Comments"])
    dfimport = dfimport.fillna('')
    dfimport = dfimport.sort_values(['Date', 'Well Name'], ascending = [False , True])
    dfimport.Date = pd.to_datetime(dfimport.Date)
    dfimport = dfimport.reset_index(drop=True)
    
    return dfimport,updates

   
def importDataEmail(start,dtype):
    end = datetime.today().date() 
    numdays = (end-start).days 
    date_list = [end - timedelta(days=x) for x in range(numdays)]
     #  Loop through dates that need production imported and try the different file name possibilities based on when the server sends the emails
    for i in range(numdays-1):
        try:
            importFile = 'custom-report-cml_' + str(date_list[i]) + '_9-00-03.csv'
            dfImport = pd.read_csv(importFile, dtype = dtype, thousands=',')
        except:
            try:
                importFile = 'custom-report-cml_' + str(date_list[i]) + '_9-00-04.csv'
                dfImport = pd.read_csv(importFile, dtype = dtype, thousands=',')
            except:
                try:
                    importFile = 'custom-report-cml_' + str(date_list[i]) + '_9-00-02.csv'
                    dfImport = pd.read_csv(importFile, dtype = dtype, thousands=',')
                except:
                    print('The file for this date does not exist')
        dfImport = dfImport.fillna('')
        dfImport.Date = pd.to_datetime(dfImport.Date)

        df = pd.concat([df,dfImport]).drop_duplicates()
        

def init():
    body = {
        "grant_type": "password",
        "client_id": client_id,
        "client_secret": client_secret,
        "username": username,
        "password": password
    }
    r=requests.post('https://api.iwell.info/v1/oauth2/access-token', headers={"content-type":"application/json"}, json = body)
    return(r.json()['access_token'])


def me(token):
    x = requests.get('https://api.iwell.info/v1/me', headers={'Authorization': f'Bearer {token}'})
    print(f'The current user is {x.json()["data"]["name"]}')

def wells(token):
    x = requests.get('https://api.iwell.info/v1/wells', headers={'Authorization': f'Bearer {token}'})
    data = x.json()['data']
    print(data[0])

def well_group(token):
    group_dict = {}
    x = requests.get('https://api.iwell.info/v1/well-groups', headers={'Authorization': f'Bearer {token}'})
    data = x.json()['data']
    [group_dict.update({i['name']: i['id']}) for i in data]
    #print("well group:",group_dict)
    return(group_dict)

def single_well_group(token, group_id):
    well_dict = {}
    x = requests.get(f'https://api.iwell.info/v1/well-groups/{group_id}/wells', headers={'Authorization': f'Bearer {token}'})
    data = x.json()['data']   
    [well_dict.update({i['name']: i['id']}) for i in data] 
    return(well_dict)

def well_production(token, well_id,time_since,cnt=[]):#time_since = 0 gives last 30 days
    cnt.append(0)
    x = requests.get(f'https://api.iwell.info/v1/wells/{well_id}/production?&since={time_since}', headers={'Authorization': f'Bearer {token}'})
    prod_data = []
    try:
        data = x.json()['data']   
        for i in data:
            prod_data.append(i)
        return prod_data,cnt,x
    except:
        return prod_data,cnt,x

def well_fields(token, well_id):
    x = requests.get(f'https://api.iwell.info/v1/wells/{well_id}/fields', headers={'Authorization': f'Bearer {token}'})
    data = x.json()['data']
    for i in data:
        print(f"{i}\n")
def well_field_value(token,well_id,field_id,time_since):
     x = requests.get(f'https://api.iwell.info/v1/wells/{well_id}/fields/{field_id}/values?since={time_since}', headers={'Authorization': f'Bearer {token}'})
     field_value = []
     data = x.json()['data']
     for i in data:
        field_value.append(i)
     return field_value

def well_comments(token, well_id,time_since):#lists from past to present
    x = requests.get(f'https://api.iwell.info/v1/wells/{well_id}/notes?since={time_since}', headers={'Authorization': f'Bearer {token}'})
    try:
        data = x.json()['data']
        comms = []
        for i in data:
            comms.append(i["message"])
        return comms
    except:
        comms = [""]
        return comms


# Save pump parameters
def pump_info():
    df_info = pd.read_excel('../CML/STprod.xlsx', sheet_name = 'Prod', usecols= 'A,I:R')
    # df_info.to_csv('example.csv', index= False)
    df_info.to_json("../STprodWebsite/STprod/static/pumpInfo.json", orient='records')

def get_formations():
    df_formations = pd.read_excel('db\\prod\\formations.xlsx')
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


def updateAwsSite(exportf, file_to_update):
    s3 = boto3.client('s3')
    with open(exportf, "rb") as f:
        s3.upload_fileobj(f, "cmlproduction", file_to_update)#update s3 bucket
    #cmd prompt to force cloudfront to check for updates
    update = 'aws cloudfront create-invalidation --distribution-id E3D76XY0BGMLIM --paths /' + file_to_update
    os.system(update)
   





# Execute program
if __name__ == '__main__':
    main()
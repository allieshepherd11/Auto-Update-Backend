import pandas as pd
from datetime import datetime, timedelta
from lxml import html
import requests
from collections import OrderedDict
import time
import os 
import boto3
from dotenv import load_dotenv
import time


def main(field):#ET / ST
    dtype = {'Oil (BBLS)': float, 'Water (BBLS)': float, 'Gas (MCF)': float, 'TP': str, 'CP': str, 'Comments': str}
    df = pd.read_csv(f'db\\prod{field}\\update\\data{field}.csv', dtype=dtype)
    df = df.fillna('')
    df.Date = pd.to_datetime(df.Date)
    df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])
    start = df.iloc[0]['Date'].date() # Gets the most recent date from the dataframe

    #Import recent data from iwell
    dfImport,updates = importDataIwell(start,field=field)
    # Update df 
    if updates:
        for i in updates:
            mask = (df['Well Name'] == i["Well Name"]) & (df['Date'] == i["date"])
            df.loc[mask, 'Oil (BBLS)'] = i["oil"]
            df.loc[mask, 'Gas (MCF)'] = i["gas"]
            df.loc[mask, 'Water (BBLS)'] = i["water"]
        

    df = pd.concat([df,dfImport]).drop_duplicates()
    df['Gas (MCF)'] = pd.to_numeric(df['Gas (MCF)'])
    df.reset_index(drop=True, inplace=True)

    # Fix blanks and clip negative values
    # df['Oil (BBLS)'].replace('',0, inplace=True)
    df['Water (BBLS)'].replace('',0, inplace=True)
    df['Gas (MCF)'].replace('',0, inplace=True)
    df['Oil (BBLS)'] = df['Oil (BBLS)'].clip(lower=0).round()
    df['Water (BBLS)'] = df['Water (BBLS)'].clip(lower=0).round()
    df['Gas (MCF)'] = df['Gas (MCF)'].clip(lower=0).round()
    df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])

    # Save to original data file
    # df.to_json(f'db\\prod{field}\\update\\data{field}.json')
    df.to_csv(f'db\\prod{field}\\update\\data{field}.csv', index=False)

    # Get 30 day moving average and append column to df
    df = df.sort_values(['Date', 'Well Name'], ascending = [True , True])
    if field == "ST": 
        df['7DMA'] = df.groupby('Well Name')['Oil (BBLS)'].transform(lambda x: x.rolling(7, 1).mean().round(1))
        df['30DMA'] = df.groupby('Well Name')['Oil (BBLS)'].transform(lambda x: x.rolling(30, 1).mean().round(1))
        df['MA Ratio'] = df['7DMA']/df['30DMA']
        df['MA Ratio'] = df['MA Ratio'].round(2)
        df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])
        ##analyze(df)
        df.drop(['30DMA', 'MA Ratio'], inplace=True, axis = 1)
    
    
    dfoil = df.groupby(['Well Name'])['Oil (BBLS)'].sum().divide(1000).astype(float).reset_index().round(1)
    dfwater = df.groupby(['Well Name'])['Water (BBLS)'].sum().divide(1000).astype(float).reset_index().round(1)
    dfgas = df.groupby(['Well Name'])['Gas (MCF)'].sum().divide(1000).astype(int).reset_index()

    dfsum = dfoil.merge(dfwater, on='Well Name').merge(dfgas, on='Well Name')
    
    # Create entries for total field production in a way that can integrate with graph
    dfoiltotal = df.groupby(['Date'])['Oil (BBLS)'].sum().astype(int).reset_index()
    dfwatertotal = df.groupby(['Date'])['Water (BBLS)'].sum().astype(int).reset_index()
    dfgastotal = df.groupby(['Date'])['Gas (MCF)'].sum().astype(int).reset_index()

    dfSTTotal = dfoiltotal.merge(dfwatertotal, on='Date').merge(dfgastotal, on='Date')
    
    title = 'South Texas Total'
    if field == "ET": title = "East Texas Total"
    dfSTTotal['Well Name'] = title
    
    dfwebsite = pd.concat([df, dfSTTotal])
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
    suff = ""
    if field == "ET": 
        suff = field
        dfsum = addFormations(dfsum)
        df_to_json_format = df_to_json_format[["Well Name", "Date", "Oil (BBLS)","Gas (MCF)", "Water (BBLS)", "TP", "CP", "Comments","Total Fluid", "DateYAxis"]]
    df_to_json_format.to_json(f"db\\prod{field}\\update\\allProductionData{suff}.json", orient='values', date_format='iso') #updating loc json file
    dfsum.to_json(f"db\\prod{field}\\update\\cumProd{suff}.json", orient='values', date_format='iso')
    #df_formations.to_json("db\\prodST\\formations.json", orient='values', date_format='iso')
    #df_info.to_json("pumpinfo.json", orient='values', date_format='iso')

    #pump_info()
    #get_formations()

## iwell Api init ##
load_dotenv()
client_id = os.getenv('client_id')
client_secret = os.getenv('client_secret')
username = os.getenv('email')
password = os.getenv('password')

### Functions ###

def importDataIwell(start,field):
    importData = []
    #unix_time_since = 1657515600#july 11 0:00
    if field == "ST": field = "SOUTH TEXAS"
    else: field = "EAST TEXAS"

    unix_time_since = time.mktime(datetime.strptime(str(start), "%Y-%m-%d").timetuple()) #unix time since last import, most recent date is removed in line 52/53. max is 30 days ago (iWell limit)
    if (datetime.today().date()-start).days > 30:
        print("too far in past")
        exit()
    token = init()
    me(token)
    wellGroup = well_group(token)
    
    st = single_well_group(token, wellGroup[field]) #All ST wells
    
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

def get_formations(field):
    df_formations = pd.read_excel(f'db\\prod{field}\\formations.xlsx')
    return df_formations
    # df_formations.to_json("C:/Users/wadmant/Desktop/OneDrive - CML Exploration/STprodWebsite/STprod/static/formations.json", orient='records')

def addFormations(df):
    df.to_csv('db\\prodET\\dfsum.json')
    df_forms = pd.read_json('db\\prodET\\formations.json')
    return df.merge(df_forms,on=0)

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
    df_analysis.to_json(
        "../STprodWebsite/STprod/static/analyze.json", orient='records')
   
# Execute program
if __name__ == '__main__':
    main("ST")
    time.sleep(60)
    main("ET")

import pandas as pd
from datetime import datetime, timedelta
from lxml import html
import requests
from collections import OrderedDict
import time
import os 
import boto3
import json
import time


def main(field):#ET / ST
    dtype = {'Oil (BBLS)': float, 'Water (BBLS)': float, 'Gas (MCF)': float, 'TP': str, 'CP': str, 'Comments': str}
    df = pd.read_csv(f'data\\prod\\{field}\\data.csv', dtype=dtype)
    df = df.fillna('')
    df.Date = pd.to_datetime(df.Date)
    df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])
    
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
    title = 'South Texas Total'
    if field == "ET": title = "East Texas Total"
    df = df[df['Well Name'] != title]
    # Save to original data file
    # df.to_json(f'db\\prod{field}\\update\\data{field}.json')
    df.to_csv(f'data\\prod\\{field}\\data.csv', index=False)
    
    # Get 30 day moving average and append column to 
    df = df.sort_values(['Date', 'Well Name'], ascending = [True , True])
        
    dfoil = df.groupby(['Well Name'])['Oil (BBLS)'].sum().divide(1000).astype(float).reset_index().round(1)
    dfwater = df.groupby(['Well Name'])['Water (BBLS)'].sum().divide(1000).astype(float).reset_index().round(1)
    dfgas = df.groupby(['Well Name'])['Gas (MCF)'].sum().divide(1000).astype(int).reset_index()
    
    #df_formations = get_formations()
    dfsum = dfoil.merge(dfwater, on='Well Name').merge(dfgas, on='Well Name')
    dfsum.loc[len(dfsum)] = dfsum[['Oil (BBLS)','Water (BBLS)','Gas (MCF)']].sum()
    dfsum.loc[len(dfsum)-1,'Well Name'] = f'{field} Total'

    title = 'South Texas Total'
    if field == "ET": title = "East Texas Total"
    df = df[df['Well Name'] != title]
    # Create entries for total field production in a way that can integrate with graph
    dfoiltotal = df.groupby(['Date'])['Oil (BBLS)'].sum().astype(int).reset_index()
    dfwatertotal = df.groupby(['Date'])['Water (BBLS)'].sum().astype(int).reset_index()
    dfgastotal = df.groupby(['Date'])['Gas (MCF)'].sum().astype(int).reset_index()
    df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])
   
    dfSTTotal = dfoiltotal.merge(dfwatertotal, on='Date').merge(dfgastotal, on='Date')
    
    dfSTTotal['Well Name'] = title
    df = pd.concat([df, dfSTTotal])
    df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])
    
    # ADD DATE COLUMN FOR X AXIS USE (DateYAxis) & CHANGING DATATYPE TO Object
    df['DateYAxis'] =  df['Date']
    df['DateYAxis'] =  pd.to_datetime(df['Date'])

    #CHANGING DATE TO OBJECT TYPE AND SPELL OUT FORMAT
    df['Date'] =  pd.to_datetime(df['Date'])
    #df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
    df['Date'] = df['Date'].dt.strftime('%B %d, %Y')
    
    #add new total fluid col, needs to last col in df to mess up js for website, or add after gas col and change graph.js to point to new indexes 
    df['Total Fluid'] = df['Oil (BBLS)'] + df['Water (BBLS)']

    if field == "ET":  df = df[["Well Name", "Date", "Oil (BBLS)","Gas (MCF)", "Water (BBLS)", "TP", "CP", "Comments", "DateYAxis","Total Fluid"]]
    mask = df['Well Name'] == title
    print(df[mask])
    df.to_json(f"data\\prod\\{field}\\data.json", orient='values', date_format='iso') #updating loc json file
    dfsum.to_json(f"data\\prod\\{field}\\cumlProd.json", orient='values', date_format='iso')
    write_formations()

    #if field == "ST": update_pumpInfo()#; analyze(pd.read_csv(f'data\\{field}\\analyze.csv'),'ST')
    return

def importDataIwell(start,field):
    #pd.set_option('display.max_rows',None)
    #pd.set_option('display.max_columns',None)

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
            comms = well_comments(token,st[well],unix_time_since)
            print(well)
        except Exception as e:
            print(e,"no data for",well)
            if len(prod[1]) % 5 == 0:
                print("sleeping...")
                time.sleep(61)
            continue
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
        cp_times = [cp[i]["updated_at"] for i in range(len(cp))]
        tp_times = [tp[i]["updated_at"] for i in range(len(tp))]

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

            data = [well,prod[0][i]["date"],prod[0][i]["oil"],prod[0][i]["gas"],prod[0][i]["water"],tp_value,cp_value]

            for c in range(len(comms)):
                dt = datetime.fromtimestamp(comms[c]['note_time']).strftime('%Y-%m-%d')
                if dt == date: 
                    data.append(comms[c]['message'])
                    break
            if len(data) == 7: data.append("")
            importData.append(data)
    with open('data.json', 'w') as f:
        json.dump(importData,f)
    print(importData)
    dfimport = pd.DataFrame(data=importData,columns=["Well Name","Date","Oil (BBLS)","Gas (MCF)","Water (BBLS)","TP","CP","Comments"])
    dfimport = dfimport.fillna('')
    dfimport = dfimport.sort_values(['Date', 'Well Name'], ascending = [False , True])
    dfimport.Date = pd.to_datetime(dfimport.Date)
    dfimport = dfimport.reset_index(drop=True)
    return dfimport,updates

def write_formations():
    df_forms_et = pd.read_json('db\\prodET\\formations.json'
                               ).rename(columns={0:"Well Name", 1 : "Formation"})
    d = pd.concat([pd.read_excel('db\\prodST\\formations.xlsx'),df_forms_et]
                    ).reset_index(drop=True).to_dict(orient='records')

    dd= {i['Well Name']:i['Formation'] for i in d}
    with open('db\\prodST\\formations.json','w') as f:
        json.dump(dd,f)

def update_pumpInfo():
    pd.read_excel("C:\\Users\\plaisancem\\OneDrive - CML Exploration\\CML\\STprod.xlsx"
                    ).drop(['Date','Notes','Oil','Gas','Water','Comments'],axis=1
                        ).to_json('db\\prodST\\update\\pumpInfo.json',orient='records')
    return 

# Return and save list of wells that are performing poorly on the
def analyze(df,field):
    schedule = pd.read_excel('C:\\Users\\plaisancem\\OneDrive - CML Exploration\\CML\\South Texas\\2023-07 OnOff Schedule.xlsx')
    mask = schedule['July Schedule'].str.contains(r'On') & schedule['July Schedule'].str.contains(r'Off')
    
    schedule = schedule[mask]
    schedule = schedule['Well Name'].tolist()
    df = df.sort_values(['Date', 'Well Name'], ascending = [True , True])
    df['7DMA'] = df.groupby('Well Name')['Oil (BBLS)'].transform(lambda x: x.rolling(7, 1).mean().round(1))
    df['30DMA'] = df.groupby('Well Name')['Oil (BBLS)'].transform(lambda x: x.rolling(30, 1).mean().round(1))
    df['MA Ratio'] = df['7DMA']/df['30DMA']
    df['MA Ratio'] = df['MA Ratio'].round(2)

    rec_date = df.sort_values('Date', ascending=False)['Date'].tolist()[0]

    unix_2ndrec = time.mktime(datetime.strptime(str(rec_date), "%Y-%m-%d").timetuple()) - 60*60*24
    datetime_2ndRec = datetime.fromtimestamp(unix_2ndrec).strftime('%Y-%m-%d')
    print(schedule)
    mask = ((df['Date'] == datetime_2ndRec) | (df['Date'] == rec_date))
    df_2nd = df[mask]
    res = []
    for idx,well in enumerate(schedule[:]):
        temp = df_2nd[df_2nd['Well Name'] == well]
        mask = temp['Oil (BBLS)'] == 0
        if  mask.all(): 
            print(mask)
            res.append(well)
    
    schedule = [item for item in schedule if item not in res]
    dfcsv = df[df['MA Ratio'] < .8]
    dfcsv.to_excel('check.xlsx',index=False)
    df_analysis = df[
        ((df['Date'] == rec_date) & (df['30DMA'] > 6) & 
        (
            ((df['MA Ratio'] < 0.8) & (df['Oil (BBLS)'] < df['30DMA'] * 0.8)) |
            (df['Oil (BBLS)'] == 0) & ~df['Well Name'].isin(schedule))
        ) | (df['Well Name'].isin(res) &(df['Date'] == rec_date) & (df['30DMA'] > 6))
    ]
    df_analysis.to_json('db\\prodST\\update\\analyzeST.json',orient='records')
   
def move():
    dfst = pd.read_json('data\\ST\\data.json')
    dfet = pd.read_json('data\\ET\\data.json')
    dfst.to_json('../frontend/data/allProductionData.json',orient='values', date_format='iso')
    dfet.to_json('../frontend/data/allProductionDataET.json',orient='values', date_format='iso')

# Execute program
if __name__ == '__main__':
    #move()
    main("ST")
    #time.sleep(60)
    #main("ET")

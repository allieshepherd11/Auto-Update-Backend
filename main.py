import pandas as pd
from datetime import datetime
import time
import json
from Report import ProdReport
from Field import Field
import webbrowser

def prod(field,abbr):
    print(f'field {field}')
    dtype = {'Oil (BBLS)': float, 'Water (BBLS)': float, 'Gas (MCF)': float, 'TP': str, 'CP': str, 'Comments': str}
    df = pd.read_csv(f'data\\prod\\{abbr}\\data.csv', dtype=dtype)
    df = df.fillna('')
    df.Date = pd.to_datetime(df.Date)
    df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])
    start = str(df.iloc[0]['Date'])[:10] # Gets the most recent date from the dataframe
    ##Import recent data from iwell
    fld = Field(field,abbr,start)
    ##
    dfImport,updates = fld.importData()
    for i in updates:
        mask = (df['Well Name'] == i["Well Name"]) & (df['Date'] == i["date"])
        df.loc[mask, ['Oil (BBLS)', 'Gas (MCF)', 'Water (BBLS)']] = i["oil"], i["gas"], i["water"]
    df = pd.concat([df,dfImport]).drop_duplicates()
    df['Oil (BBLS)'] = pd.to_numeric(df['Oil (BBLS)'], errors='coerce')

    df['Oil (BBLS)'] = pd.to_numeric(df['Oil (BBLS)'])
    df['Gas (MCF)'] = pd.to_numeric(df['Gas (MCF)'])
    df.reset_index(drop=True, inplace=True)
    df['Water (BBLS)'].replace('',0, inplace=True)
    df['Gas (MCF)'].replace('',0, inplace=True)
    df['Oil (BBLS)'] = df['Oil (BBLS)'].clip(lower=0).round(1)
    df['Water (BBLS)'] = df['Water (BBLS)'].clip(lower=0).round()
    df['Gas (MCF)'] = df['Gas (MCF)'].clip(lower=0).round()
    
    #fld specific tasks
    if fld.abbr == 'GC': df = handleGC(df)
    if fld.abbr == 'NM': df = handleNM(df)
    if fld.abbr == 'ST': recYrProd(df,fld.abbr)
    if fld.abbr == 'WT': df = handleWT(df)
    title = f'{fld.field} Total' if fld.field != 'West TX' else 'West Texas Total'
    

    title = title.title()
    
    df = df[df['Well Name'] != title]
    df['Well Name'] = df['Well Name'].str.title()
    wnMap = {'Cr #101': 'CR #101','Cr #201': 'CR #201','Cr #301': 'CR #301',
             'Cr #302': 'CR #302','Cr #401': 'CR #401','Cr #501': 'CR #501',
             'Cr #939': 'CR #939','Jj #1': 'JJ #1','Ct #1': 'CT #1','Jic #1': 'JIC #1',
             'Jic Buda #1': 'JIC Buda #1','Lt #1': 'LT #1','Mdb #1': 'MDB #1','Pc #1': 'PC #1',
             'Rab #1': 'RAB #1','Rab #2': 'RAB #2','Rab #3': 'RAB #3','Bmmp #1': 'BMMP #1',
             'Bruce Weaver #2 Re': 'Bruce Weaver #2 RE','Vre Minerals #1':'VRE Minerals #1',
             'Dial #1 St': 'Dial #1 ST', 'Ra #1': 'RA #1','Ck #1': 'CK #1', 'Clary Rb #1': 'Clary RB #1',
             'Mcduffie Unit #1': 'McDuffie Unit #1', 'Mt Unit #1H': 'MT Unit #1H', 'Ws #1': 'WS #1',
             'Ee 12 #1': 'EE 12 #1','Jm Moore': 'JM Moore','Cl Moore 12': 'CL Moore 12','Ab Pad 10 St. #1': 'AB Pad 10 State #1',
             'Cw 14 State #1': 'CW 14 State #1','Blair Txl #1': 'Blair TXL #1','Blair Txl #2': 'Blair TXL #2',
             'Blair Txl #3': 'Blair TXL #3','Llb 15 #1': 'LLB 15 #1','South Juwf': 'South JUWF', 'North Juwf':'North JUWF',
             'Triple A Federal #3': 'Triple A Fed #3','Cmww #1':'CMWW #1','Cmww #2':'CMWW #2'}
    
    for k,v in wnMap.items(): df.loc[df['Well Name'] == k,'Well Name'] = v
    df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])
    df.to_csv(f'data\\prod\\{fld.abbr}\\data.csv', index=False)
    if fld.abbr == 'ET': df.to_csv('data\\prod\\WB\\data.csv', index=False)
    df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])
    dfoil = df.groupby(['Well Name'])['Oil (BBLS)'].sum().divide(1000).astype(float).reset_index().round(1)
    dfwater = df.groupby(['Well Name'])['Water (BBLS)'].sum().divide(1000).astype(float).reset_index().round(1)
    dfgas = df.groupby(['Well Name'])['Gas (MCF)'].sum().divide(1000).astype(int).reset_index().round(1)
    

    dfsum = dfoil.merge(dfwater, on='Well Name').merge(dfgas, on='Well Name')
    dfsum.loc[len(dfsum)] = dfsum[['Oil (BBLS)','Water (BBLS)','Gas (MCF)']].sum()
    dfsum.loc[len(dfsum)-1,'Well Name'] = f'{fld.abbr} Total'

    # Create entries for total field production in a way that can integrate with graph
    dfoiltotal = df.groupby(['Date'])['Oil (BBLS)'].sum().astype(int).reset_index()
    dfwatertotal = df.groupby(['Date'])['Water (BBLS)'].sum().astype(int).reset_index()
    dfgastotal = df.groupby(['Date'])['Gas (MCF)'].sum().astype(int).reset_index()

    dfTotal = dfoiltotal.merge(dfwatertotal, on='Date').merge(dfgastotal, on='Date')
    dfTotal['Well Name'],dfTotal['TP'],dfTotal['CP'],dfTotal['Comments'] = title.title(),"","",""
    
    df = pd.concat([df, dfTotal])
    df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])
    df = df.reset_index(drop=True)
    df['7DMA'] = df.groupby('Well Name')['Oil (BBLS)'].transform(lambda x: x.rolling(7, 1).mean().round(1))
   
    # ADD DATE COLUMN FOR X AXIS USE (DateYAxis) & CHANGING DATATYPE TO Object
    df['DateYAxis'] =  df['Date']
    df['DateYAxis'] =  pd.to_datetime(df['Date'])

    #CHANGING DATE TO OBJECT TYPE AND SPELL OUT FORMAT
    df['Date'] =  pd.to_datetime(df['Date'])
    df['Date'] = df['Date'].dt.strftime('%B %d, %Y')
    
    df['Total Fluid'] = df['Oil (BBLS)'] + df['Water (BBLS)']
    df = df[["Well Name", "Date", "Oil (BBLS)","Gas (MCF)", "Water (BBLS)", "TP", "CP", "Comments","DateYAxis","Total Fluid","7DMA"]]
  
    df.to_json(f"data\\prod\\{fld.abbr}\\data.json", orient='values', date_format='iso') #updating loc json file
    dfsum.to_json(f"data\\prod\\{fld.abbr}\\cuml.json", orient='values', date_format='iso')

    #if fld.abbr == "ST": update_pumpInfo(); analyze(pd.read_csv(f'data\\prod\\{fld.abbr}\\data.csv'),'ST')

    return

def write_formations():
    df_forms_et = pd.read_json('db\\prodET\\formations.json'
                               ).rename(columns={0:"Well Name", 1 : "Formation"})
    d = pd.concat([pd.read_excel('db\\prodST\\formations.xlsx'),df_forms_et]
                    ).reset_index(drop=True).to_dict(orient='records')

    dd= {i['Well Name']:i['Formation'] for i in d}
    with open('data\\misc\\formations.json','w') as f:
        json.dump(dd,f)

def update_pumpInfo():
    pd.read_excel("C:\\Users\\plaisancem\\OneDrive - CML Exploration\\CML\\STprod.xlsx"
                    ).drop(['Date','Notes','Oil','Gas','Water','Comments'],axis=1
                        ).to_json('data\\prod\\ST\\pumpInfo.json',orient='records')
    return 

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
    for _,well in enumerate(schedule[:]):
        temp = df_2nd[df_2nd['Well Name'] == well]
        mask = temp['Oil (BBLS)'] == 0
        if  mask.all(): 
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
    df_analysis.to_json('data\\prod\\ST\\analyze.json',orient='records')

def move(field):
    paths = {f'data\\prod\\{field}\\cuml.json': f'../frontend/data/{field}/cumlProd{field}.json',
             f'data\\prod\\{field}\\data.json': f'../frontend/data/{field}/prod{field}.json',
             f'data\\prod\\{field}\\analyze.json': f'../frontend/data/{field}/analyze{field}.json',
             }
    try:
        for k,v in paths.items(): pd.read_json(k).to_json(v,orient='values',date_format='iso')
    except FileNotFoundError as err:
        print(err)
    if field == 'ST': pd.read_json('data\\prod\\ST\\pumpinfo.json').to_json('../frontend/data/ST/pumpInfo.json',orient='records',date_format='iso')
    return   

def moProd(field):
    # group by Well Name, Year, and Month
    df_daily = pd.read_csv(f"data\prod\{field}\data.csv")
    df_daily['Date'] = pd.to_datetime(df_daily['Date'])
    df_daily['Month'] = df_daily['Date'].dt.month
    df_daily['Year'] = df_daily['Date'].dt.year
    grouped = df_daily.groupby(['Well Name', 'Year', 'Month'])
    print(df_daily)
    # sum up production from each month
    monthly_sum = grouped.sum(['Oil (BBLS)', 'Gas (MCF)', 'Water (BBLS)']).reset_index()
    monthly_sum['Date'] = pd.to_datetime(monthly_sum[['Year', 'Month']].assign(day=1))
    monthly_sum = monthly_sum.drop('Year', axis=1)
    monthly_sum = monthly_sum.drop('Month', axis=1)

    # group by Year, and Month
    df_day = pd.read_csv(f"data\prod\{field}\data.csv")
    df_day['Date'] = pd.to_datetime(df_day['Date'])
    df_day['Month'] = df_day['Date'].dt.month
    df_day['Year'] = df_day['Date'].dt.year
    grouped = df_day.groupby(['Year', 'Month'])

    # sum up production from each month field
    mo_sum = grouped.sum(['Oil (BBLS)', 'Gas (MCF)', 'Water (BBLS)']).reset_index()
    mo_sum['Date'] = pd.to_datetime(mo_sum[['Year', 'Month']].assign(day=1))
    mo_sum = mo_sum.drop('Year', axis=1)
    mo_sum = mo_sum.drop('Month', axis=1)

    mo_sum['Well Name'] = 'South Texas Total' if field == 'ST' else 'East Texas Total'

    df_final = pd.concat([monthly_sum, mo_sum])
    df_final = df_final.sort_values('Date').reset_index(drop=True)

    df_final.to_csv(f"data\prod\{field}\moData.csv", index=False) 
    df_final.to_json(f"../frontend/data/{field}/dataMonthly{field}.json", orient='values', date_format='iso')

def recYrProd(df:pd.DataFrame,field):
    df = df.copy()
    data = {"Date": [], "New Prod": [] , "Tot Prod": [], 'percent' : []}
    _365 = 60*60*24*365

    df['Date'] = pd.to_datetime(df['Date'])

    first_prod = df.groupby('Well Name')['Date'].min()
    first_prod = first_prod.apply(lambda x: int(x.timestamp()))
    first_prod = first_prod.to_dict()
    dates = sorted(list(set(df["Date"].tolist())))

    for date in dates:
        prod_today = 0
        totprod_today = 0
        data["Date"].append(date)

        unix = int(date.timestamp())
        mask = (df["Date"] == date) 
        df_date = df[mask]

        for _,row in df_date.iterrows():
            totprod_today += row["Oil (BBLS)"]
            day1 = first_prod[row["Well Name"]]
            if day1 > (unix - _365):
                prod_today += row["Oil (BBLS)"]
        data["New Prod"].append(prod_today)
        data["Tot Prod"].append(totprod_today)
        if totprod_today != 0: percent = 100*(prod_today/totprod_today)
        else : percent = 0
        data["percent"].append(round(percent))


    pd.DataFrame(data).to_csv(f'data/prod/{field}/recYrProd.csv',index=False)
    pd.DataFrame(data).to_csv( f'../frontend/data/{field}/recYrProd.csv',index=False)

def handleGC(df:pd.DataFrame) -> pd.DataFrame:
    df.loc[df['Well Name'] == 'JM MOORE','Well Name'] = 'JM Moore'
    mask = (df['Well Name'].str.contains("JM Moore"))
    jms = ['JM Moore 178','JM Moore 192','JM Moore Main Battery','JM Moore Test Battery']

    ds = set(df['Date'].tolist()); ds = list(ds)
    for d in ds:
        mask = ((df['Well Name'].isin(jms)) & (df['Date'] == d))
        if not mask.any(): continue
        jmdf = df[mask]
        sums = jmdf[['Oil (BBLS)', 'Gas (MCF)','Water (BBLS)']].sum()
        tp = jmdf.loc[jmdf['Well Name'] == 'JM Moore 192', 'TP'].tolist()[0]
        cp = jmdf.loc[jmdf['Well Name'] == 'JM Moore 192', 'CP'].tolist()[0]
        c192 = jmdf.loc[jmdf['Well Name'] == 'JM Moore 192', 'Comments'].tolist()[0]; c178 = jmdf.loc[jmdf['Well Name'] == 'JM Moore 178', 'Comments'].tolist()[0]
        comm192 = c192 if c192 != 'nan' else ''
        comm178 = c178 if c178 != 'nan' else ''
        entry = {'Well Name':'JM Moore','Date':d,'Oil (BBLS)':sums['Oil (BBLS)'],'Gas (MCF)':sums['Gas (MCF)'],
                    'Water (BBLS)':sums['Water (BBLS)'],'TP':tp,'CP':cp,'Comments':f'192: {comm192} 178: {comm178}'}
        entry = {k:[v] for k,v in entry.items()}
        df = pd.concat([df,pd.DataFrame(entry)])

    df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])
    rm = ['Dyer 2 Sales Tap','Jm Moore 92 Swd','Moore Cl 10 Swd']
    for i in jms: rm.append(i)
    mask = ~df['Well Name'].isin(rm)

    return df[mask]

def handleNM(df:pd.DataFrame) -> pd.DataFrame:
    rm = ["Cooper 24 Federal #2 SWD","Nathaniel 29 St #1","Mcwf #1", "MCWF #1"]
    return df[~df['Well Name'].isin(rm)]

def handleWT(df:pd.DataFrame) -> pd.DataFrame:
    wells:list(str) = ['Blair TXL 7 #1','Blair TXL 7 #2', 'Blair TXL 7 #3']
    for well in wells:
        mask = df["Well Name"] == well
        df.loc[mask, 'Well Name'] = well.replace("7",'').replace(' #','#')
    df.loc[df['Well Name'] == 'Davis Lease','Well Name'] = 'Davis 3'
    return df

def lstProd(field,day):#day YYYY-MM-dd
    df = pd.read_csv(f'data\prod\{field}\data.csv')

    wells = sorted(set(df['Well Name'].tolist()))
    wells = [w for w in wells if w not in pd.read_csv('data/prod/lastprod/shutins.csv')['Well'].tolist()]

    res = {'Well Name':[],'Last Production': [],f'Days since {day}':[]}
    for well in wells:
        mask = (df['Well Name'] == well) & (df['Oil (BBLS)'] + df['Gas (MCF)'] != 0)
        dfwell = df[mask].reset_index(drop=True).sort_values(['Date'], ascending = [False])
        d = dfwell.iloc[0]['Date'] if mask.any() else None
        days = None
        if d is not None:
            unix_since = int(datetime.strptime(day, "%Y-%m-%d").timestamp()) - int(datetime.strptime(d, "%Y-%m-%d").timestamp()) 
            days = round(unix_since/(60*60*24))
        res['Well Name'].append(well);res['Last Production'].append(d);res[f'Days since {day}'].append(days)

    pd.DataFrame(res).to_csv(f'data\prod\lastProd\lastprod{field}.csv',index=False)


if __name__ == '__main__':
    for abbr,field in {'ST':'SOUTH TEXAS','ET':'EAST TEXAS','GC':'Gulf Coast','WT':'West TX','NM':'New Mexico'}.items():
        prod(field=field,abbr=abbr); move(field=abbr)
#       ProdReport(field=abbr,title=field).genReport()
 #       webbrowser.open_new_tab(f'C:\\Users\\plaisancem\\Documents\\dev\\prod_app\\backend\\data\\prod\\{abbr}\\report.pdf')
  #  ProdReport(field='WB',title='Woodbine').genReport()
   # webbrowser.open_new_tab(f'C:\\Users\\plaisancem\\Documents\\dev\\prod_app\\backend\\data\\prod\\WB\\report.pdf')
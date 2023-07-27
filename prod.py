import pandas as pd
from datetime import datetime
import time
import json
import time
from Report import ProdReport
from Field import Field


def main(field,abbr):
    dtype = {'Oil (BBLS)': float, 'Water (BBLS)': float, 'Gas (MCF)': float, 'TP': str, 'CP': str, 'Comments': str}
    df = pd.read_csv(f'data\\prod\\{abbr}\\data.csv', dtype=dtype)
    df = df.fillna('')
    df.Date = pd.to_datetime(df.Date)
    df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])
    start = str(df.iloc[0]['Date'])[:10] # Gets the most recent date from the dataframe
    ##Import recent data from iwell
    fld = Field(field,abbr,start)
    
    dfImport,updates = fld.importData()
    for i in updates:
        mask = (df['Well Name'] == i["Well Name"]) & (df['Date'] == i["date"])
        df.loc[mask, 'Oil (BBLS)'] = i["oil"]
        df.loc[mask, 'Gas (MCF)'] = i["gas"]
        df.loc[mask, 'Water (BBLS)'] = i["water"]
        

    df = pd.concat([df,dfImport]).drop_duplicates()
    df['Oil (BBLS)'] = pd.to_numeric(df['Oil (BBLS)'], errors='coerce')
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

    title = f'{fld.field} Total'
    df = df[df['Well Name'] != title]
    # Save to original data file
    df.to_csv(f'data\\prod\\{fld.abbr}\\data.csv', index=False)
    # Get 30 day moving average and append column to df
    df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])
        
    dfoil = df.groupby(['Well Name'])['Oil (BBLS)'].sum().divide(1000).astype(float).reset_index().round(1)
    dfwater = df.groupby(['Well Name'])['Water (BBLS)'].sum().divide(1000).astype(float).reset_index().round(1)
    dfgas = df.groupby(['Well Name'])['Gas (MCF)'].sum().divide(1000).astype(int).reset_index()
    
    #df_formations = get_formations()

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
    
    # ADD DATE COLUMN FOR X AXIS USE (DateYAxis) & CHANGING DATATYPE TO Object
    df['DateYAxis'] =  df['Date']
    df['DateYAxis'] =  pd.to_datetime(df['Date'])

    #CHANGING DATE TO OBJECT TYPE AND SPELL OUT FORMAT
    df['Date'] =  pd.to_datetime(df['Date'])
    #df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
    df['Date'] = df['Date'].dt.strftime('%B %d, %Y')
    
    #add new total fluid col, needs to last col in df to mess up js for website, or add after gas col and change graph.js to point to new indexes 
    df['Total Fluid'] = df['Oil (BBLS)'] + df['Water (BBLS)']

    if fld.abbr == "ET": df = df[["Well Name", "Date", "Oil (BBLS)","Gas (MCF)", "Water (BBLS)", "TP", "CP", "Comments","DateYAxis","Total Fluid"]]
    
    df.to_json(f"data\\prod\\{fld.abbr}\\data.json", orient='values', date_format='iso') #updating loc json file
    dfsum.to_json(f"data\\prod\\{fld.abbr}\\cuml.json", orient='values', date_format='iso')
    #write_formations()

    if fld.abbr == "ST": update_pumpInfo(); analyze(pd.read_csv(f'data\\prod\\{fld.abbr}\\data.csv'),'ST')
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
    df_analysis.to_json('data\\prod\\ST\\analyze.json',orient='records')

def move(field):
    paths = {f'data\\prod\\{field}\\cuml.json': f'../frontend/data/cumlProd{field}.json',
             f'data\\prod\\{field}\\data.json': f'../frontend/data/allProductionData{field}.json',
             f'data\\prod\\{field}\\analyze.json': f'../frontend/data/analyze{field}.json',
             }
    try:
        for k,v in paths.items(): pd.read_json(k).to_json(v,orient='values',date_format='iso')
    except FileNotFoundError as err:
        print(err)
    if field == 'ST': pd.read_json('data\\prod\\ST\\pumpinfo.json').to_json('../frontend/data/pumpInfo.json',orient='records',date_format='iso')
    return   

def moProd(field):
    # group by Well Name, Year, and Month
    df_daily = pd.read_csv(f"data\prod\{field}\data.csv")
    df_daily['Date'] = pd.to_datetime(df_daily['Date'])
    df_daily['Month'] = df_daily['Date'].dt.month
    df_daily['Year'] = df_daily['Date'].dt.year
    grouped = df_daily.groupby(['Well Name', 'Year', 'Month'])

    # sum up production from each month
    monthly_sum = grouped.sum().reset_index()
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
    mo_sum = grouped.sum().reset_index()
    mo_sum['Date'] = pd.to_datetime(mo_sum[['Year', 'Month']].assign(day=1))
    mo_sum = mo_sum.drop('Year', axis=1)
    mo_sum = mo_sum.drop('Month', axis=1)

    mo_sum['Well Name'] = 'South Texas Total' if field == 'ST' else 'East Texas Total'

    df_final = pd.concat([monthly_sum, mo_sum])
    df_final = df_final.sort_values('Date').reset_index(drop=True)

    df_final.to_csv(f"data\prod\{field}\moData.csv", index=False) 
    df_final.to_json(f"../frontend/data/dataMonthly{field}.json", orient='values', date_format='iso')

if __name__ == '__main__':
    #for ABBR,FIELD in {'ST':'SOUTH TEXAS','ET':'EAST TEXAS'}.items(): main(field=FIELD,abbr=ABBR); move(field=ABBR);time.sleep(60)
    #for ABBR,FIELD in {'GC':'Gulf Coast','WT':'West TX'}.items(): main(field=FIELD,abbr=ABBR); move(field=ABBR);time.sleep(60)
    main('New Mexico','NM'); move('NM')
    



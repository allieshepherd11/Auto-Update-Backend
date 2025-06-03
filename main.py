import pandas as pd
import numpy as np
import openpyxl
import xlwings as xw
from datetime import datetime
import time
import json
from src.Modules.Report import ProdReport
from src.Modules.Field import Field,generateMnthArray
import webbrowser
import numpy as np
import re
import src.Modules.Tanks as Tanks
from collections import defaultdict
from src.Modules.OutlookBot import ReportBot
import shutil
import os
from src.Modules.Logger import Logger
import io


def updateApp(field,importProd=True,takeToday=False):
    print(field)
    abbr = ''.join([w[0] for w in field.split(' ')]).upper()
    dtype = {'Oil (BBLS)': float, 'Water (BBLS)': float, 'Gas (MCF)': float, 'TP': str, 'CP': str, 'Comments': str}
    df = pd.read_csv(f'data/prod/{abbr}/data.csv', dtype=dtype,na_values=[''])
    df.Date = pd.to_datetime(df.Date)
    df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])
    start = str(df.iloc[0]['Date'])[:10] # Gets the most recent date from the dataframe
    ##Import recent data from iwell
    ##
    if importProd:
        fld = Field(field=field,abbr=abbr,start=start,takeToday=takeToday)
        dfImport,updates,tank_levels,dfGasImport = fld.importData()
        with open(f"data/prod/{abbr}/batteries.json",'w') as f: json.dump(tank_levels,f)
        for i in updates:
            mask = (df['Well Name'] == i["Well Name"]) & (df['Date'] == i["date"])
            df.loc[mask, ['Oil (BBLS)', 'Gas (MCF)', 'Water (BBLS)']] = i["oil"], i["gas"], i["water"]
        df = pd.concat([df,dfImport]).drop_duplicates()

        if len(dfGasImport) > 0:
            dfGasImport = dfGasImport.sort_values(['Date', 'Well Name'], ascending = [False , True])
            dfGasImport['Date'] = pd.to_datetime(dfGasImport['Date'])
            
            df = pd.merge(df, dfGasImport, on=['Date', 'Well Name'], how='left', suffixes=('', '_y'))
            df['Sales Pressure'] = df['Sales Pressure'].combine_first(df['Sales Pressure_y'])
            df['Flow Rate Sales'] = df['Flow Rate Sales'].combine_first(df['Flow Rate Sales_y'])
            df['Flow Rate Flare'] = df['Flow Rate Flare'].combine_first(df['Flow Rate Flare_y'])
            df.drop(['Flow Rate Sales_y', 'Flow Rate Flare_y','Sales Pressure_y'], axis=1, inplace=True)
            df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])
            #print(df.loc[df['Well Name'] == 'Aaron #1'][:20])
            #exit()

    df['Oil (BBLS)'] = pd.to_numeric(df['Oil (BBLS)'], errors='coerce')

    df['Oil (BBLS)'] = pd.to_numeric(df['Oil (BBLS)'])
    df['Gas (MCF)'] = pd.to_numeric(df['Gas (MCF)'])
    df.reset_index(drop=True, inplace=True)
    df['Water (BBLS)'] = df['Water (BBLS)'].replace('',0)
    df['Gas (MCF)'] = df['Gas (MCF)'].replace('',0)
    df['Oil (BBLS)'] = df['Oil (BBLS)'].clip(lower=0).round()
    df['Water (BBLS)'] = df['Water (BBLS)'].clip(lower=0).round()
    df['Gas (MCF)'] = df['Gas (MCF)'].clip(lower=0).round()
    
    #fld specific tasks
    if abbr == 'GC': df = handleGC(df)
    if abbr == 'NM': df = handleNM(df)
    if abbr == 'ST': recYrProd(df,abbr)
    if abbr == 'WT': df = handleWT(df)
    title = f'{field} Total' if field != 'West TX' else 'West Texas Total'

    title = title.title()
    
    df = df[df['Well Name'] != title]
    df['Well Name'] = df['Well Name'].str.title()
    if field != 'IW':
        with open("data/misc/wnMap.json",'r') as f: wnMap = json.load(f)
        for k,v in wnMap.items(): df.loc[df['Well Name'] == k,'Well Name'] = v
    df['Well Name'] = df['Well Name'].str.replace(' Re',' RE')
    
    df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])
    df.to_csv(f'data/prod/{abbr}/data.csv', index=False)
    if abbr == 'ET': df.to_csv('data/prod/WB/data.csv', index=False)
    df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])


    # Create entries for total field production in a way that can integrate with graph
    dfoiltotal = df.groupby(['Date'])['Oil (BBLS)'].sum().astype(int).reset_index()
    dfwatertotal = df.groupby(['Date'])['Water (BBLS)'].sum().astype(int).reset_index()
    dfgastotal = df.groupby(['Date'])['Gas (MCF)'].sum().astype(int).reset_index()

    dfTotal = dfoiltotal.merge(dfwatertotal, on='Date').merge(dfgastotal, on='Date')
    dfTotal['Well Name'],dfTotal['TP'],dfTotal['CP'],dfTotal['Comments'] = title.title(),"","",""
    df = pd.concat([df, dfTotal])
    #group entries
    groups = {"Group Marpick Comp": ['Lander #1','RAB #1','RAB #2','RAB #3','Chad #1','Kiley #1','JJ #1','J Beeler #1','Aaron #1','Pfeiffer Byrd #1',
                                     'Jessica #1','Pickwill #1','Marpick #1','Gail #1','Marguerite #1','Eileen #1','Richard #1','Beeler Ranch #1','Annpick #1'], 
            "Group Glass Rods": ['JJ #1','J Beeler #1'],
            "Group Moreland Comp":[
                "CMWW #1","CMWW #2","Cannan #1","Circle T #1","Lochte #1"," CT #1","Burns Ranch #1","Thalmann #1 RE","Evergreen #1","Gil #1"
            ],
            "Group Molak Comp":{
                "Barrier #1","Charles B #1","Molak #1","Bond #1","Bermuda #1","Blas Reyes #1","Big Sonny #1","Russell #1","Dillard #1"
                ,"Sugarland #1","Trotter #1","Ruth #1","Dunlap #1","Verna #1","La Rosita #1 RE","Richardson #1",
            },
            "Group Sour Wells":{
                "Aaron #1","Beeler Ranch #1","Carolyn #1","Chad #1","Gail #1","J Beeler #1","JIC #1","JJ #1","Jospeh #1","Kiley #1","Kliemann #1",
                "Lamb #1","Lander #1","Marrs #1","Parkway #1 RE","Pecan Grove #1","RAB #1", "RAB #2","RAB #3","Whittington #1"
            }
            }
    if abbr == 'ST':
        for groupName,wells in groups.items():
            dfgroup = df[df['Well Name'].isin(wells)]
            dfoiltotal = dfgroup.groupby(['Date'])['Oil (BBLS)'].sum().astype(int).reset_index()
            dfwatertotal = dfgroup.groupby(['Date'])['Water (BBLS)'].sum().astype(int).reset_index()
            dfgastotal = dfgroup.groupby(['Date'])['Gas (MCF)'].sum().astype(int).reset_index()
            dfsales = dfgroup.groupby(['Date'])['Flow Rate Sales'].sum().astype(int).reset_index()
            dfflare = dfgroup.groupby(['Date'])['Flow Rate Flare'].sum().astype(int).reset_index()
            dfline = dfgroup.groupby(['Date'])['Sales Pressure'].mean().reset_index()

            dfTotal = dfoiltotal.merge(dfwatertotal, on='Date').merge(dfgastotal, on='Date').merge(dfsales, on='Date') \
                .merge(dfflare, on='Date').merge(dfline, on='Date')
            dfTotal['Well Name'],dfTotal['TP'],dfTotal['CP'],dfTotal['Comments'] = groupName,"","",""

            df = pd.concat([df, dfTotal])

    dfoil = df.groupby(['Well Name'])['Oil (BBLS)'].sum().divide(1000).astype(float).reset_index().round(1)
    dfwater = df.groupby(['Well Name'])['Water (BBLS)'].sum().divide(1000).astype(float).reset_index().round(1)
    dfgas = df.groupby(['Well Name'])['Gas (MCF)'].sum().divide(1000).astype(int).reset_index().round(1)
    dfsum = dfoil.merge(dfwater, on='Well Name').merge(dfgas, on='Well Name')
    #dfsum.loc[len(dfsum)] = dfsum[['Oil (BBLS)','Water (BBLS)','Gas (MCF)']].sum()
    #dfsum.loc[len(dfsum)-1,'Well Name'] = f'{abbr} Total'
    #print(dfsum)
    #print(dfsum.loc[dfsum['Well Name'] == 'South Texas Total'].iloc[0])
    #exit()

    df['Total Fluid'] = df['Oil (BBLS)'] + df['Water (BBLS)']
    df = df.sort_values(['Date', 'Well Name'], ascending = [True , True]).reset_index(drop=True)
    df['7DMA Oil'] = df.groupby('Well Name')['Oil (BBLS)'].rolling(window=7).mean().reset_index(level=0, drop=True).round(1)
    df['7DMA Fluid'] = df.groupby('Well Name')['Total Fluid'].rolling(window=7).mean().reset_index(level=0, drop=True).round(1)
    df['30DMA Oil'] = df.groupby('Well Name')['Oil (BBLS)'].rolling(window=30).mean().reset_index(level=0, drop=True).round(1)
    df['Accum Oil'] = df.groupby('Well Name')['Oil (BBLS)'].cumsum()

    df['WC'] = df['Water (BBLS)'] / df['Total Fluid']
    df['7DMA WC'] = df.groupby('Well Name')['WC'].rolling(window=7,min_periods=1).mean().reset_index(level=0, drop=True).round(3)
    df['7DMA WC'] = df['7DMA WC']*100
    df = df.sort_values(['Date', 'Well Name'], ascending = [False , True]).reset_index(drop=True)
    # ADD DATE COLUMN FOR X AXIS USE (DateYAxis) & CHANGING DATATYPE TO Object
    df['DateYAxis'] =  df['Date']
    df['DateYAxis'] =  pd.to_datetime(df['Date'])

    #CHANGING DATE TO OBJECT TYPE AND SPELL OUT FORMAT
    df['Date'] =  pd.to_datetime(df['Date'])
    df['Date'] = df['Date'].dt.strftime('%B %d, %Y')
    
    colsOrder = ["Well Name", "Date", "Oil (BBLS)","Gas (MCF)", "Water (BBLS)", "TP", "CP", "Comments",
                 "DateYAxis","Total Fluid","7DMA Oil","7DMA Fluid","30DMA Oil","Accum Oil",'WC','7DMA WC']
    if abbr == 'ST':
        colsOrder.extend(["Sales Pressure","Flow Rate Sales","Flow Rate Flare"])

    df = df[colsOrder]
    
    if abbr == 'ST':
        with open("data/misc/excludeWells.json",'r') as f: excludeWells = json.load(f)[abbr]
        dfOldWells = df.loc[df['Well Name'].isin(excludeWells)].reset_index(drop=True)
        df=df.loc[~df['Well Name'].isin(excludeWells)].reset_index(drop=True)
        dfOldWells.to_json('../frontend/data/ST/pluggedData.json', orient='values', date_format='iso')

    dfpre2004 = pd.read_csv('data/misc/pre2004Cumls.csv')
    for _,row in dfpre2004.iterrows():
        mask = dfsum['Well Name'].str.lower() == row['Well Name'].lower()
        if not mask.empty:
            dfsum.loc[mask,['Oil (BBLS)','Gas (MCF)']] += row['Oil']/1000,row['Gas']/1000

    #updating loc json file
    df.to_json(f"data/prod/{abbr}/data.json", orient='values', date_format='iso')
    dfsum.to_json(f"data/prod/{abbr}/cuml.json", orient='values', date_format='iso')
    
    if abbr == 'ST' or abbr == 'ET':
        with open('../frontend/data/misc/recentProdDate.json','r+') as f:
            data = json.load(f)
            data[abbr.upper()] = str(df.iloc[0]['Date']).strip()[:-6]
            f.seek(0)
            json.dump(data, f)
            f.truncate()

    #if abbr == 'ST' and importProd: Tanks.run()
    if abbr == 'ST' or abbr == 'ET':
        try:
            updateApp_tam(abbr,f'data/misc/{abbr}/TAM_update_2025-03-17.csv')

            analyze(abbr)
        except Exception as err:
            print(f'ONE DRIVE ERROR {err}')
    
    mnthlyProd(field)
    move(abbr)
    formatStackedGraph(abbr)
    return

def parse_schedule(df_prod:pd.DataFrame) -> pd.DataFrame:
    #df_prod = df_prod[df_prod['Total Fluid'] != 0].sort_values(by='Datetime',ascending=False).reset_index(drop=True)
    #df_prod = df_prod.groupby('Well Name').first().drop([col for col in df_prod.columns if col not in ['Well Name', 'Date']],axis=1)
    #df_prod['Date'] = pd.to_datetime(df_prod['Date'])
    #df_prod['Days Since Prod'] = (datetime.now() - df_prod['Date']).dt.days - 1

    curr_mnth = datetime.now().strftime("%Y-%m")
    #curr_mnth = '2024-01'
    df = pd.read_excel(f'C:/Users/plaisancem/CML Exploration/Travis Wadman - CML/South Texas/{curr_mnth} OnOff Schedule.xlsx').iloc[:,:2]
    df = df.rename(columns={el:idx for idx,el in enumerate(df.columns)})
    shutins = df.loc[df[1].str.contains("shut",case=False)][0].tolist()
    df = df[((df[1].str.contains("on",case=False)) & (df[1].str.contains("off",case=False)))]

    df['On'] = df[1].str.extract(r'(\d+)\s+on',flags=re.IGNORECASE)
    df['Off'] = df[1].str.extract(r'(\d+)\s+off',flags=re.IGNORECASE)
    #df = df.rename(columns={0:'Well Name'})
    #df = pd.merge(df,df_prod,on='Well Name',how='left').drop([1,'Date'],axis=1)
    return df

def analyze(fieldAbbr) -> pd.DataFrame:
    df = pd.read_json(f'data/prod/{fieldAbbr}/data.json')
    cols = ["Well Name", "Date", "Oil (BBLS)","Gas (MCF)", "Water (BBLS)", "TP", "CP", "Comments","Datetime","Total Fluid","7DMA Oil","7DMA Fluid","30DMA Oil"
            ,"Accum Oil","WC","WC 7DMA","Line Pressure","Sales Rate","Flare Rate"]
    df = df.rename(columns={idx:el for idx,el in enumerate(cols)})
    past_days = df.sort_values('Datetime', ascending=False)['Datetime'].tolist()
    #df['MA Ratio Oil'] = df['7DMA Oil'] / df['30DMA Oil']
    df['MA Ratio Oil'] = np.where(df['30DMA Oil'] != 0, df['7DMA Oil'] / df['30DMA Oil'], 1)
    df['7DMA Flare'] = df.groupby('Well Name')['Flare Rate'].rolling(window=7).mean().reset_index(level=0, drop=True).round(1)

    scheduled = parse_schedule(df) if fieldAbbr == 'ST' else list()

    conditions = {
        'Low MA Oil': (df["MA Ratio Oil"] < .7),
        'No Fluids': (df['Total Fluid'] == 0),
        'No Oil': (df['Oil (BBLS)'] == 0),
        'High Flare':(df['Flare Rate'] > 50) | (df['7DMA Flare'] > 30)
    }
    
    mask = ((conditions["Low MA Oil"] | conditions["No Fluids"] | conditions['No Oil'] | conditions['High Flare']) & ~(df['30DMA Oil'] == 0))
    df_analyze = df.loc[df['Datetime'] == past_days[0]].loc[mask].reset_index(drop=True)

    #add case names        
    df_analyze['Low MA Oil'] = (df_analyze["MA Ratio Oil"] < .7)
    df_analyze['No Fluids'] = (df_analyze['Total Fluid'] == 0)
    df_analyze['No Oil'] = (df_analyze['Oil (BBLS)'] == 0)
    df_analyze['High Flare'] = (df_analyze['Flare Rate'] > 50) | (df['7DMA Flare'] > 30)


    df_analyze['case'] = df_analyze \
                    .apply(lambda row: [condition for condition in conditions.keys() if row[condition]], axis=1)
    #remove scheduled if 
    for _,row in scheduled.iterrows(): 
        row_match = df_analyze.loc[df_analyze['Well Name'] == row[0]]
        if not row_match.empty:
            df_well = df.loc[df['Well Name'] == row[0]]
            days=0#cant use comments, no consistency 
            for _,r in df_well.iterrows():
               if r['Total Fluid'] != 0: break
               else: days += 1
            if (days <= int(row['Off']) and row_match['No Fluids'].tolist()[0]):
                if 'High Flare' in row_match['case'].tolist()[0]:
                    df_analyze.loc[df_analyze['Well Name'] == row[0], 'case'] = df_analyze.loc[df_analyze['Well Name'] == row[0], 'case'].apply(lambda x: ['High Flare'])

                else:
                    df_analyze=df_analyze.drop(row_match.index)

    df_analyze = df_analyze[df_analyze['Well Name'] != 'Thalmann #1']
    df_analyze = df_analyze.drop(conditions.keys(),axis=1).reset_index(drop=True)   
    print(df_analyze)         
    df_analyze.to_json(f'data/prod/{fieldAbbr}/analyze.json', orient='values', date_format='iso')
    df_analyze.to_json(f'../frontend/data/{fieldAbbr}/analyze{fieldAbbr}.json', orient='values', date_format='iso')

def write_formations():
    df_forms_et = pd.read_json('db/prodET/formations.json'
                               ).rename(columns={0:"Well Name", 1 : "Formation"})
    d = pd.concat([pd.read_excel('db/prodST/formations.xlsx'),df_forms_et]
                    ).reset_index(drop=True).to_dict(orient='records')

    dd= {i['Well Name']:i['Formation'] for i in d}
    with open('data/misc/formations.json','w') as f:
        json.dump(dd,f)

def updateApp_tam(abbr,importPath):
    
    def import_tam_data(importPath):
        dfimport = pd.read_csv(importPath)
        df = pd.read_csv('./data/misc/ST/tam.csv')
        df = pd.concat([df,dfimport]).reset_index(drop=True)
        df.to_csv('./data/misc/ST/tam.csv',index=False)
        print(df)
        df['Date'] = pd.to_datetime(df['Date'] + ' ' + df['Time'],format='mixed')

        df_fl = df[(~df['Distance to Liquid (ft)'].isna()) & (df['Well State'] == 'Producing')].reset_index(drop=True)
        df_dyno = df[(~df['Strokes Per Minute (SPM)'].isna())].reset_index(drop=True)

        df_fl.to_json(f'../frontend/data/ST/fls.json', orient='values', date_format='iso')

        df_fl = df_fl.loc[df_fl.groupby('Well Name')['Date'].idxmax()]
        df_dyno = df_dyno.loc[df_dyno.groupby('Well Name')['Date'].idxmax()]

        file_path = "C:/Users/plaisancem/CML Exploration/Travis Wadman - CML/STprod.xlsx"
        wb = openpyxl.load_workbook(file_path)
        sheet_stprod = wb['Prod']  
    
        dfstprod = pd.read_excel(file_path)
        def well_name_key(x):
            if x == x:
                x=x.lower().replace('#', '').replace(' ', '')
            return x
        df_fl['Well Name'] = df_fl['Well Name'].apply(lambda x: well_name_key(x))
        df_dyno['Well Name'] = df_dyno['Well Name'].apply(lambda x: well_name_key(x))
        dfstprod['Key'] = dfstprod['Well Name'].apply(lambda x: well_name_key(x))

        
        for _, row in df_fl.iterrows():
            mask = row['Well Name'] == dfstprod['Key']
            dfstprod.loc[mask, ['FL Date', 'GFLAP']] = row['Date'], row['Gas Free Above Pump (ft)']
        
        for _, row in df_dyno.iterrows():
                mask = row['Well Name'] == dfstprod['Key']
                #if not mask.any():
                #    print(row['Well Name'])
                dfstprod.loc[mask, ['SPM', 'DH SL', 'EPT']] = row['Strokes Per Minute (SPM)'], \
                                                        row['Maximum Plunger Stroke (in)'], row['Effective Plunger Travel (in)']

        dfstprod['FL Date'] = pd.to_datetime(dfstprod['FL Date']).dt.date

        for idx, row in dfstprod.iterrows():
            well_name_col = 'A' 
            fl_date_col = 'K'   
            gflap_col = 'L'      
            spm_col = 'E'
            dhsl_col = 'F'
            ept_col = 'H'

            well_name_cell = sheet_stprod[f'{well_name_col}{idx + 2}']  # Header row
            fl_date_cell = sheet_stprod[f'{fl_date_col}{idx + 2}']
            gflap_cell = sheet_stprod[f'{gflap_col}{idx + 2}']

            spm_cell = sheet_stprod[f'{spm_col}{idx + 2}']
            dhsl_cell = sheet_stprod[f'{dhsl_col}{idx + 2}']
            ept_cell = sheet_stprod[f'{ept_col}{idx + 2}']


            if well_name_cell.value == row['Well Name']:
                fl_date_cell.value = row['FL Date']
                gflap_cell.value = row['GFLAP']
                spm_cell.value = row['SPM']
                dhsl_cell.value = row['DH SL']
                ept_cell.value = row['EPT']


        wb.save(file_path)

    if abbr == 'ST':import_tam_data(importPath)
    path = "C:/Users/plaisancem/CML Exploration/Travis Wadman - CML/STprod.xlsx" if abbr == 'ST' \
        else "C:/Users/plaisancem/CML Exploration/Travis Wadman - CML/East Texas/East Texas Production Tracker.xlsx"
    tempPath = "C:/Users/plaisancem/Downloads/prod-copy.xlsx"
    shutil.copyfile(path, tempPath)
    df = pd.read_excel(tempPath)
    
    if os.path.exists(tempPath):
        os.remove(tempPath)

    def c(diam):
        if diam == 2:
            return .466
        elif diam == 1.75:
            return .357
        elif diam == 1.5:
            return .262
        elif diam == 1.25:
            return .182
        elif diam == 1.06:
            return .132
        elif diam == 2.25:
            return .59

    diacol = 'Plunger Diameter (in)' if abbr == 'ST' else 'Pump Diameter'
    df['C'] = df[diacol].apply(lambda x: c(x))
    df['Ideal bfpd'] = round(df['DH SL']*df['SPM']*df['C'],0)
    df = df.drop([col for col in df.columns if col not in ['Well Name','Last WO Date','C','SPM','DH SL','Ideal bfpd','Pump Depth','GFLAP','FL Date','Inc']],axis=1)
    df['Last WO Date'] =  pd.to_datetime(df['Last WO Date'])
    df['FL Date'] =  pd.to_datetime(df['FL Date'])
    df['Days since WO'] = (pd.Timestamp.now() - df['Last WO Date']).dt.days

    df['Last WO Date'] = df['Last WO Date'].dt.strftime('%Y-%m-%d')
    
    df['FL Date'] = df['FL Date'].dt.strftime('%Y-%m-%d')
    if abbr == 'ST':
        df.loc[len(df)] = {'Well Name':'Tortuga Unit B 2Re','GFLAP':1626,'FL Date':'2024-08-18'}
    print(df['Well Name'].tolist())
    df.to_json(f'data/prod/{abbr}/pumpinfo.json',orient='records',date_format='iso')
    df.to_json(f'../frontend/data/{abbr}/pumpInfo.json',orient='records',date_format='iso')

    return df

def move(fieldAbbr):
    paths = {f'data/prod/{fieldAbbr}/cuml.json': f'../frontend/data/{fieldAbbr}/cumlProd{fieldAbbr}.json',
             f'data/prod/{fieldAbbr}/data.json': f'../frontend/data/{fieldAbbr}/prod{fieldAbbr}.json',
             f'data/prod/{fieldAbbr}/analyze.json': f'../frontend/data/{fieldAbbr}/analyze{fieldAbbr}.json',
             }
    try:
        for k,v in paths.items(): pd.read_json(k).to_json(v,orient='values',date_format='iso')
    except FileNotFoundError as err:
        print(err)
    if fieldAbbr == 'ST': pd.read_json('data/prod/ST/pumpinfo.json').to_json('../frontend/data/ST/pumpInfo.json',orient='records',date_format='iso')
    return   

def mnthlyProd(field):
    abbr = ''.join([w[0] for w in field.split(' ')]).upper()

    # group by Well Name, Year, and Month
    df_daily = pd.read_csv(f"data/prod/{abbr}/data.csv")
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
    df_day = pd.read_csv(f"data/prod/{abbr}/data.csv")
    df_day['Date'] = pd.to_datetime(df_day['Date'])
    df_day['Month'] = df_day['Date'].dt.month
    df_day['Year'] = df_day['Date'].dt.year
    grouped = df_day.groupby(['Year', 'Month'])

    # sum up production from each month field
    mo_sum = grouped.sum(['Oil (BBLS)', 'Gas (MCF)', 'Water (BBLS)']).reset_index()
    mo_sum['Date'] = pd.to_datetime(mo_sum[['Year', 'Month']].assign(day=1))
    mo_sum = mo_sum.drop('Year', axis=1)
    mo_sum = mo_sum.drop('Month', axis=1)

    mo_sum['Well Name'] = f'{field} Total'

    df_final = pd.concat([monthly_sum, mo_sum])
    df_final = df_final.sort_values('Date').reset_index(drop=True)

    df_final.to_csv(f"data/prod/{abbr}/moData.csv", index=False) 
    df_final.to_json(f"../frontend/data/{abbr}/dataMonthly{abbr}.json", orient='values', date_format='iso')

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
    jms = ['JM Moore 178','JM Moore Main Battery','JM Moore Test Battery']

    ds = set(df['Date'].tolist()); ds = list(ds)
    for d in ds:
        mask = ((df['Well Name'].isin(jms)) & (df['Date'] == d))
        if not mask.any(): continue
        jmdf = df[mask]
        sums = jmdf[['Oil (BBLS)', 'Gas (MCF)','Water (BBLS)']].sum()

        c178 = jmdf.loc[jmdf['Well Name'] == 'JM Moore 178', 'Comments'].tolist()[0]
        c_main = jmdf.loc[jmdf['Well Name'] == 'JM Moore Main Battery', 'Comments'].tolist()[0]
        c_test = jmdf.loc[jmdf['Well Name'] == 'JM Moore Test Battery', 'Comments'].tolist()[0]

        comm178 = c178 if c178 != 'nan' else ''
        comm_main = c_main if c_main != 'nan' else ''
        comm_test = c_test if c_test != 'nan' else ''

        entry = {'Well Name':'JM Moore','Date':d,'Oil (BBLS)':sums['Oil (BBLS)'],'Gas (MCF)':sums['Gas (MCF)'],
                    'Water (BBLS)':sums['Water (BBLS)'],'TP':0,'CP':0,'Comments':f'Test Bat: {comm_test} Main Bat: {comm_main} 178: {comm178}'}
        
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
    df = pd.read_csv(f'data/prod/{field}/data.csv')

    wells = sorted(set(df['Well Name'].tolist()))
    wells = [w for w in wells if w not in pd.read_csv('data/prod/IW/data.csv')['Well Name'].tolist()]

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
    rm_wells = ['Christopher #1','Davis Ozelle Unit 1 H','Wendel #1','Wickson Unit #1','North Twinberry 5 State #1','Raider 9 St #2']
    df = df.loc[~df['Well Name'].isin(rm_wells)]
    pd.DataFrame(res).to_csv(f'data/prod/reports/lastprod/{field} Last Production since {day}.csv',index=False)

def move_well_IW(field_abbr,well):
    df = pd.read_csv(f'data/prod/{field_abbr}/data.csv')
    df_IW = pd.read_csv(f'data/prod/IW/data.csv')
    mask = df['Well Name'] == well
    if mask.any():
        df = df.loc[mask]
    else:
        print('Well',well,'NOT FOUND')
    df_IW = pd.concat([df_IW,df]).drop_duplicates()
    df_IW = df_IW.sort_values(['Date', 'Well Name'], ascending = [False , True])

    print(df_IW)
    df_IW.to_csv('data/prod/IW/data.csv',index=False)
    updateApp('Inactive Wells',0,0)
    return

def cml_prod_report():
    dfs =pd.DataFrame()
    with open('data/prod/IW/field.json', 'r') as f:
        iw_fields = json.load(f)

    for idx,f in enumerate(['SOUTH TEXAS','EAST TEXAS','GULF COAST','WEST TEXAS','NEW MEXICO','INACTIVE WELLS']):
        abbr = ''.join([w[0] for w in f.split(' ')]).upper()
        df = pd.read_csv(f'data/prod/{abbr}/data.csv')
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.loc[(df['Date'] >= '3/1/2024') & (df['Date'] <= '2/28/2025')]
        if abbr != 'IW':
            df['Field'] = f
        else:
            df['Field'] = df['Well Name'].apply(lambda x: iw_fields.get(x,'')) 
        dfs = pd.concat([dfs,df])
        
    dfs = dfs.loc[dfs['Well Name'] != 'Tortuga Unit B 2Re']

    dfs.to_excel('CML Production 3-1-24 thru 2-28-25.xlsx',index=False)
    return

def formatStackedGraph(abbr):
    df = pd.read_csv(f'data/prod/{abbr}/data.csv')
    first_prod = {}
    data_formated = {}
    for well,df_well in df.groupby('Well Name'):
        
        data_formated[well] = {
            "x":df_well['Date'].tolist(),
            "oil":df_well['Oil (BBLS)'].tolist()
        }
        first_prod[well] = pd.to_datetime(df_well['Date']).min().strftime('%Y-%m-%d')

    with open(f'C:/Users/plaisancem/Documents/Dev/Apps/Prod/frontend/data/{abbr}/stackedGraph.json', 'w') as f:
        json.dump(data_formated,f)
    with open(f'C:/Users/plaisancem/Documents/Dev/Apps/Prod/frontend/data/{abbr}/firstProdDate.json', 'w') as f:
        json.dump(first_prod,f)
    return

def automated_report(receipent,wells):
    #receipent = 'PlaisanceM@cmlexp.com'

    bot = ReportBot(recipient=receipent,wells=wells)
    relativePath,reportTitle = bot.genReport()
    
    attachments = [rf"C:\Users\plaisancem\Documents\Dev\Apps\Prod\backend\{relativePath['pdf']}",
                   rf"C:\Users\plaisancem\Documents\Dev\Apps\Prod\backend\{relativePath['csv']}"]
    bot.sendEmail(to_address=receipent,
                  subject=reportTitle,
                  body=f'Automated Report for {receipent.split('@')[-1].split('.')[0].upper()}\n\nThank you\nMatthew Plaisance\n512-971-9722\nCML Exploration LLC',
                  attachments_paths=attachments,
                  bcc_address='PlaisanceM@cmlexp.com'
                  )
    return

if __name__ == '__main__':
    #updateApp_tam('ST','data\misc\ST\TAM 5-12-25.csv')
    #exit()
    #move_well_IW('ST','Dial #1 ST')
    #for abbr in ['ST','ET','GC','WT','NM']:
    #    lstProd(abbr,'2025-05-05')
    #exit()
    #updateApp_tam('ST','data\misc\ST\TAM_update_2025-03-17.csv')
    for idx,f in enumerate(['SOUTH TEXAS','EAST TEXAS','Gulf Coast','West TX','New Mexico']):
        updateApp(field=f,importProd=1,takeToday=0)
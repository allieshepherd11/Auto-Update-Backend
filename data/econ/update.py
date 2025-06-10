import pandas as pd
from datetime import datetime, timedelta
import os
import json
from collections import defaultdict

def payoutsHist():
    def parse_file(root,tar):
        excel_file = pd.ExcelFile(root + tar)

        dfs = []
        sheet_names = excel_file.sheet_names
        for sheet_name in sheet_names:
            if sheet_name in ['Georgetown Wells','Buda Wells','Austin Chalk Wells','Others']:

                df = excel_file.parse(sheet_name)
                print(df)
                df = df[[df.columns[0],'Unnamed: 21']]
                df = df.rename(columns={df.columns[0]: 'Well Name','Unnamed: 21':'% Payout'}).dropna().reset_index(drop=True)
                monthStr = tar.split('.')[0].replace('Payouts','').strip()
                df['Month'] = datetime.strptime(monthStr, "%Y-%m").replace(day=1).date().strftime('%Y-%m-%d')
                dfs.append(df)
        return dfs

    dfs = []
    root = "C:/Users/plaisancem/CML Exploration/Travis Wadman - CML/P&L's/"
    for obj in os.listdir(root):
        if len(obj.split('.')) > 1:#file
            if 'payout' in obj.lower():
                for df in parse_file(root,obj): dfs.append(df)
        else:
            for f in os.listdir(root+obj):
                if 'payout' in f.lower():
                    for df in parse_file(root+obj+'/',f): dfs.append(df)
    df = pd.concat(dfs, ignore_index=True) \
        .sort_values(['Well Name','Month'], ascending = [True,False]).reset_index(drop=True)
    df = df[df['Well Name'] != 'Well Name']
    df.loc[df['Well Name'] == 'Margurite #1','Well Name'] = "Marguerite #1"
    res = defaultdict(dict)
    for well,group in df.groupby('Well Name'):
        wellName = well.replace('#','').lower()
        for _,row in group.iterrows():
            res[wellName][row['Month']] = row['% Payout']

    with open("C:\\Users\\plaisancem\\Documents\\dev\\Apps\\Prod\\frontend\\data\\econ\\payoutHistory.json", 'w') as f:
        json.dump(res,f)

def payouts(field,mnth):
    excel_file = pd.ExcelFile(f"C:/Users/plaisancem/CML Exploration/Travis Wadman - CML/P&L's/{mnth} Payouts.xlsx")
    sheet_names = excel_file.sheet_names
    dfs = []
    field_sheets = {'South Texas Only':['Georgetown Wells','Buda Wells','Austin Chalk Wells','Others'],
                    'East Texas':['Brazos','Grimes','Madison','Robertson','Others'],
                    'East Texas Woodbine':['Brazos','Grimes','Madison','Robertson','Others'],
                    'Gulf Coast':[''],
                    'West TexasNM':['West TX','NM']
                    }
    
    for sheet_name in sheet_names:
        if sheet_name in field_sheets[field]:
            i = 19 if sheet_name == 'Georgetown Wells' else 20
            df = excel_file.parse(sheet_name)
            df = df[[df.columns[0],f'Unnamed: {i}']]
            df = df.rename(columns={df.columns[0]: 'Well Name',f'Unnamed: {i}':'% Payout'}).dropna().reset_index(drop=True)
            dfs.append(df)
    if len(dfs) > 0:
        df = pd.concat(dfs, ignore_index=True) \
            .sort_values(['Well Name'], ascending = [True]).reset_index(drop=True)
        df = df[df['Well Name'] != 'Well Name']
        df.loc[df['Well Name'] == 'Margurite #1','Well Name'] = "Marguerite #1"
        df.loc[df['Well Name'] == 'Beeler #16H RE','Well Name'] = "Beeler #16 RE"
        
        with open('data/econ/data/rename.json', 'r') as f:
            data = json.load(f)
        for k,v in data.items():
            df.loc[df['Well Name'] == k,'Well Name'] = v
    
    else:
        df = pd.DataFrame()
    title = 'payouts' if field == 'South Texas Only' else f'payouts {field}'

    

    df.to_json(f"C:\\Users\\plaisancem\\Documents\\dev\\Apps\\Prod\\frontend\\data\\econ\\{title}.json", orient='records')
    return df

def economics(field,mnth,mnthIgnore):
    #mnth = 'Jan 2024'
    p = f"C:/Users/plaisancem/CML Exploration/Travis Wadman - CML/P&L's/2025 PL'S By Well {field} - Copy.xlsx"
    df = pd.read_excel(p,sheet_name='Prospect & Well Listing')

    df.columns = df.iloc[0].reset_index(drop=True)

    rec_mnth_dt = (datetime.strptime(mnth, '%b %Y').replace(day=1) + timedelta(days=32))\
                        .replace(day=1) - timedelta(days=1)
    mnthIgnore_dt = (datetime.strptime(mnthIgnore, '%b %Y').replace(day=1) + timedelta(days=32))\
                        .replace(day=1) - timedelta(days=1)

    df = df.drop([col for col in df.columns if col not in ['Well List:','YTD Gain/Loss',rec_mnth_dt,mnthIgnore_dt]],axis=1)
    df = df.rename(columns={rec_mnth_dt:'Recent Month P&L','Well List:':'Well Name'})
    df = df.sort_values(['Well Name'], ascending = [True]).reset_index(drop=True)
    df['Date'] = mnth
    df = df.dropna()
    df = df[df['Well Name'] != 'Well List:']

    
    if 'Jan' not in mnthIgnore:#last mnth of year
        df['YTD P&L'] = df['YTD Gain/Loss'] - df[mnthIgnore_dt]
    else:
        df['YTD P&L'] = df['YTD Gain/Loss']
        
    with open('data/econ/data/rename.json', 'r') as f:
        data = json.load(f)
    for k,v in data.items():
        df.loc[df['Well Name'] == k,'Well Name'] = v

    df.to_json(f'./data/econ/data/{field}.json',orient='records')
    df.to_json(f'C:\\Users\\plaisancem\\Documents\\dev\\Apps\\Prod\\frontend\\data\\econ\\economics{field}.json',orient='records')
    return df

def combine(fields):
    root='data/econ/data/'
    res=[]
    for f in fields:
        with open(f'{root+f}.json', 'r') as f:
            data = json.load(f)
        res.extend(data)
    
    with open(root+'economics.json', 'w') as f:
        json.dump(res,f)
    with open(f'C:/Users/plaisancem/Documents/dev/Apps/Prod/frontend/data/econ/economics.json', 'w') as f:
        json.dump(res,f)

if __name__ == '__main__':
    currMnth = datetime.now().strftime('%Y-%m')
    revMnth = (datetime.now() - timedelta(days=60)).strftime('%b %Y')
    billMnth = (datetime.now() - timedelta(days=30)).strftime('%b %Y')
    print("revMnth",revMnth)
    print("billMnth",billMnth)

    fields = ['South Texas Only','East Texas','East Texas Woodbine','Gulf Coast','West TexasNM']
    df_econ = pd.DataFrame()
    df_payout = pd.DataFrame()
    for idx,field in enumerate(fields):
        #if idx == 0:continue
        print(field)
        #df_payout = pd.concat([df_payout,payouts(field,currMnth)])
        df_econ = pd.concat([df_econ,economics(field,revMnth,billMnth)])
    df_econ.to_json(f'C:\\Users\\plaisancem\\Documents\\dev\\Apps\\Prod\\frontend\\data\\econ\\economics.json',orient='records')
    df_payout.to_json(f'C:\\Users\\plaisancem\\Documents\\dev\\Apps\\Prod\\frontend\\data\\econ\\payouts.json',orient='records')

    #combine()
    
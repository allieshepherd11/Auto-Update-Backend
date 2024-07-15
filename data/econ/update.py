import pandas as pd
from datetime import datetime, timedelta
import os
import json

def payoutsHist():
    def parse_file(root,tar):
        excel_file = pd.ExcelFile(root + tar)

        dfs = []
        sheet_names = excel_file.sheet_names
        for sheet_name in sheet_names:
            if sheet_name in ['Georgetown Wells','Buda Wells','Austin Chalk Wells','Others']:

                df = excel_file.parse(sheet_name)
                df = df[[df.columns[0],'Unnamed: 19']]
                df = df.rename(columns={df.columns[0]: 'Well Name','Unnamed: 19':'% Payout'}).dropna().reset_index(drop=True)
                df['Month'] = tar.split('.')[0].replace('Payouts','').strip()
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
    print(dfs)
        
    df = pd.concat(dfs, ignore_index=True) \
        .sort_values(['Well Name'], ascending = [True]).reset_index(drop=True)
    df = df[df['Well Name'] != 'Well Name']
    df.loc[df['Well Name'] == 'Margurite #1','Well Name'] = "Marguerite #1"
    df.to_json("C:\\Users\\plaisancem\\Documents\\dev\\Apps\\Prod\\frontend\\data\\econ\\payoutHistory.json", orient='records')

def payouts(field,mnth):
    excel_file = pd.ExcelFile(f"C:/Users/plaisancem/CML Exploration/Travis Wadman - CML/P&L's/{mnth} Payouts.xlsx")
    sheet_names = excel_file.sheet_names
    dfs = []
    for sheet_name in sheet_names:
        if sheet_name in ['Georgetown Wells','Buda Wells','Austin Chalk Wells','Others']:

            df = excel_file.parse(sheet_name)
            df = df[[df.columns[0],'Unnamed: 19']]
            df = df.rename(columns={df.columns[0]: 'Well Name','Unnamed: 19':'% Payout'}).dropna().reset_index(drop=True)
            dfs.append(df)
    df = pd.concat(dfs, ignore_index=True) \
        .sort_values(['Well Name'], ascending = [True]).reset_index(drop=True)
    df = df[df['Well Name'] != 'Well Name']
    df.loc[df['Well Name'] == 'Margurite #1','Well Name'] = "Marguerite #1"
    df.loc[df['Well Name'] == 'Beeler #16H RE','Well Name'] = "Beeler #16 RE"

    df.to_json("C:\\Users\\plaisancem\\Documents\\dev\\Apps\\Prod\\frontend\\data\\econ\\payouts.json", orient='records')

def economics(field,mnth,mnthIgnore):
    #mnth = 'Jan 2024'
    df = pd.read_excel(f"C:/Users/plaisancem/CML Exploration/Travis Wadman - CML/P&L's/2024 PL'S By Well {field} - Copy.xlsx")

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
    df['YTD P&L'] = df['YTD Gain/Loss'] - df[mnthIgnore_dt]
    with open('data/econ/data/rename.json', 'r') as f:
        data = json.load(f)
    for k,v in data.items():
        df.loc[df['Well Name'] == k,'Well Name'] = v



    df.to_json(f'./data/econ/data/{field}.json',orient='records')
    df.to_json(f'C:\\Users\\plaisancem\\Documents\\dev\\Apps\\Prod\\frontend\\data\\econ\\economics{field}.json',orient='records')

def combine():
    root='data/econ/data/'
    res=[]
    for f in ['East Texas Woodbine.json','South Texas Only.json','East Texas.json']:
        print(f)
        with open(root+f, 'r') as f:
            data = json.load(f)
        res.extend(data)
    
    with open(root+'economics.json', 'w') as f:
        json.dump(res,f)
    with open(f'C:/Users/plaisancem/Documents/dev/Apps/Prod/frontend/data/econ/economics.json', 'w') as f:
        json.dump(res,f)
    return

if __name__ == '__main__':
    #payoutsHist()
    #payouts('2024-04')#2024-01
    currMnth = datetime.now().strftime('%Y-%m')
    revMnth = (datetime.now() - timedelta(days=60)).strftime('%b %Y')
    billMnth = (datetime.now() - timedelta(days=30)).strftime('%b %Y')
    economics('South Texas Only',revMnth,billMnth)
    economics('East Texas',revMnth,billMnth)
    economics('East Texas Woodbine',revMnth,billMnth)
    payouts('',currMnth)
    combine()
    
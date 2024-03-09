import pandas as pd
from datetime import datetime, timedelta

def payouts():
    excel_file = pd.ExcelFile('data\econ\\2024-03 Payouts.xlsx')

    sheet_names = excel_file.sheet_names
    dfs = []
    for sheet_name in sheet_names:
        if sheet_name in ['Georgetown Wells','Buda Wells','Austin Chalk Wells']:

            df = excel_file.parse(sheet_name)
            df = df[[df.columns[0],'Unnamed: 19']]
            df = df.rename(columns={df.columns[0]: 'Well Name','Unnamed: 19':'% Payout'}).dropna().reset_index(drop=True)
            dfs.append(df)
    df = pd.concat(dfs, ignore_index=True) \
        .sort_values(['Well Name'], ascending = [True]).reset_index(drop=True)
    df = df[df['Well Name'] != 'Well Name']
    df.loc[df['Well Name'] == 'Margurite #1','Well Name'] = "Marguerite #1"
    df.to_json("C:\\Users\\plaisancem\\Documents\\dev\\Apps\\Prod\\frontend\\data\\econ\\payouts.json", orient='records')

def economics():
    df = pd.read_excel("data\econ\\2024 PL'S By Well South Texas Only - Copy.xlsx")

    df.columns = df.iloc[0].reset_index(drop=True)
    rec_mnth = 'Jan 2024'

    rec_mnth_dt = (datetime.strptime(rec_mnth, '%b %Y').replace(day=1) + timedelta(days=32))\
                        .replace(day=1) - timedelta(days=1)
    print(rec_mnth_dt)
    df = df.drop([col for col in df.columns if col not in ['Well List:','YTD Gain/Loss',rec_mnth_dt]],axis=1)
    df = df.rename(columns={rec_mnth_dt:'Recent Month P&L','Well List:':'Well Name','YTD Gain/Loss':'YTD P&L'})
    print(df)
    df = df.sort_values(['Well Name'], ascending = [True]).reset_index(drop=True)
    df['Date'] = rec_mnth
    df = df.dropna()
    df.loc[df['Well Name'] == 'BRUCE WEAVER #2','Well Name'] = "BRUCE WEAVER #2 RE"
    df.loc[df['Well Name'] == 'Pfeifer #1','Well Name'] = "Pfeiffer #1"
    df.loc[df['Well Name'] == 'La Rosita #1','Well Name'] = "La Rosita #1 Re"


    df.to_json('C:\\Users\\plaisancem\\Documents\\dev\\Apps\\Prod\\frontend\\data\\econ\\economics.json',orient='records')


payouts()
economics()
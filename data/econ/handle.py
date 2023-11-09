import pandas as pd
from datetime import datetime, timedelta

def payouts():
    excel_file = pd.ExcelFile('data\econ\payoutsNov23.xlsx')

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
    print(df)
    df.to_json("C:\\Users\\plaisancem\\Documents\\dev\\prod_app\\frontend\\data\\econ\\payouts1.json", orient='records')
payouts()
def economics():
    df = pd.read_excel("data\econ/2023PLST.xlsx")

    df.columns = df.iloc[0]
    df = df[1:]
    print(df)

    rec_mnth = 'Sep 2023'

    rec_mnth_dt = (datetime.strptime(rec_mnth, '%b %Y').replace(day=1) + timedelta(days=32))\
                        .replace(day=1) - timedelta(days=1)
    print(rec_mnth_dt)
    df = df.drop([col for col in df.columns if col not in ['Well List:','YTD Gain/Loss',rec_mnth_dt]],axis=1)
    df = df.rename(columns={rec_mnth_dt:'Recent Month P&L','Well List:':'Well Name','YTD Gain/Loss':'YTD P&L'})
    df = df.sort_values(['Well Name'], ascending = [True]).reset_index(drop=True)
    df['Date'] = rec_mnth
    df = df.dropna()
    df.loc[df['Well Name'] == '"BRUCE WEAVER #2','Well Name'] = "BRUCE WEAVER #2 RE"
    print(df)
    df.to_json('C:\\Users\\plaisancem\\Documents\\dev\\prod_app\\frontend\\data\\econ\\economics.json',orient='records')
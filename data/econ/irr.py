import pandas as pd

def fetchDrillingCosts():
    excel_file = pd.ExcelFile(f'data\econ\\2024-04 Payouts.xlsx')
    sheet_names = excel_file.sheet_names
    dfs = []
    for sheet_name in sheet_names:
        if sheet_name in ['Georgetown Wells','Buda Wells','Austin Chalk Wells','Others']:

            df = excel_file.parse(sheet_name)
            df = df[[df.columns[0],'Unnamed: 11','Unnamed: 19']]
            df = df.rename(columns={df.columns[0]: 'Well Name','Unnamed: 11':'Completion Total','Unnamed: 19':'% Payout'}).dropna().reset_index(drop=True)
            dfs.append(df)
    df = pd.concat(dfs, ignore_index=True) \
        .sort_values(['Well Name'], ascending = [True]).reset_index(drop=True)
    df.to_csv('data/econ/data/completionTotal.csv',index=False)

if __name__ == "__main__":
    fetchDrillingCosts()
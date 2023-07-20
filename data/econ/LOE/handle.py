import pandas as pd


def LOEtrend(LOE):
    files = ['2018','2019','2020','2021','2022']
    dfs = {}
    for file in files:
        df = pd.read_csv(f'db\\econ\\LOE\\{file}LOE.csv')
        df['Date'] = pd.date_range(start=f'1/1/{file}', periods=12, freq='MS').strftime('%b %y')
        dfs[file] = df
    print(dfs['2022'])

if __name__ == "__main__":
    LOEtrend(' LOE - SALT WATER DISPOSAL')
    
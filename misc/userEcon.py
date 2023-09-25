import pandas as pd


def addMonth(month):
    df = pd.read_json('data/econ/plData.json',orient='values').T
    print(df)
    newmonth = pd.read_json(f'data\econ\pl{month}23.json')
    n = []
    for idx,row in newmonth.iterrows():
        mask = row['Well Name'].upper() == df['Well Name']
        if not mask.any():print(f"NONE {row['Well Name'].upper()}");n.append(row['Well Name'].upper())
        df.loc[mask,f'{month} 23'] = row['Recent Month P&L']
    print(df)
    print(sorted(n))
    return

addMonth('Jun')
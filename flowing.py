import pandas as pd
import datetime

df = pd.read_csv('data1.csv')
print(f'df {df}')

res = {}
data = {"Date": [], "New Prod": []}
_365 = 60*60*24*365

df['Date'] = pd.to_datetime(df['Date'])

first_prod = df.groupby('Well Name')['Date'].min()
first_prod = first_prod.apply(lambda x: int(x.timestamp()))
first_prod = first_prod.to_dict()

dates = sorted(list(set(df["Date"].tolist())))

for date in dates:
    res[date] = {}
    prod_today = 0
    data["Date"].append(date)

    unix = int(date.timestamp())
    mask = (df["Date"] == date) 
    df_date = df[mask]

    for idx,row in df_date.iterrows():
        day1 = first_prod[row["Well Name"]]
        if day1 > (unix - _365):
            res[date][row["Well Name"]] = row["Oil (BBLS)"]
            prod_today += row["Oil (BBLS)"]
    data["New Prod"].append(prod_today)
print(f'res :: {res}')
dfr = pd.DataFrame(res)
print(f'data : {data}')
dfd = pd.DataFrame(data)
dfr.to_csv('./recProd.csv')
dfd.to_csv('./recProd1.csv',index=False)

print(dfr)
print(dfr['2023-06-05'])
print(dfd)
exit()
for idx,row in df.iterrows():
    res[row['Date']] = 0
    unix = int(row["Date"].timestamp())
    print(unix)
    mask = df["Date"]
    

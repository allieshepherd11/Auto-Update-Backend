import pandas as pd

df = pd.read_csv('data/prod/ST/data.csv')
data = {"Date": [], "New Prod": [] , "Tot Prod": [], 'percent' : []}
_365 = 60*60*24*365

df['Date'] = pd.to_datetime(df['Date'])

first_prod = df.groupby('Well Name')['Date'].min()
print(first_prod)
first_prod.to_csv('firstprod.csv')
first_prod = first_prod.apply(lambda x: int(x.timestamp()))
first_prod = first_prod.to_dict()
import pandas as pd
from collections import defaultdict
import json

df_192 = pd.read_csv(r"C:\Users\plaisancem\Downloads\jm moore 192.csv")
df_gc = pd.read_csv('data/prod/GC/data.csv')
df_gc.loc[df_gc['Comments'] == '0', 'Comments'] = ''
df_gc = df_gc.loc[~((df_gc['Well Name'] == 'Jm Moore #192') & (df_gc['Date'] < '2015-12-01'))]


df_gc.to_csv('data/prod/GC/data.csv',index=False)

exit()
df_192['Well Name'] = 'JM Moore #192'
df_192['TP'] = 50
df_192['CP'] = 50

df_192['Date'] = pd.to_datetime(df_192['Date'])
df_gc['Date'] = pd.to_datetime(df_gc['Date'])

df_192 = df_192.drop(columns=['Gas Flare (MCF)'])

print(df_192.columns)
print(df_gc.columns)

df = pd.concat([df_gc,df_192])
df = df.sort_values(['Date', 'Well Name'], ascending = [False , True]).reset_index(drop=True)

print(df)
df = df.fillna(0)
df['Oil (BBLS)'] = df['Oil (BBLS)'].astype(int)

value_to_subtract = df.loc[df['Well Name'] == 'JM Moore #192', 'Oil (BBLS)'].iloc[0]
df.loc[df['Well Name'] == 'JM Moore', 'Oil (BBLS)'] -= value_to_subtract

value_to_subtract = df.loc[df['Well Name'] == 'JM Moore #192', 'Water (BBLS)'].iloc[0]
df.loc[df['Well Name'] == 'JM Moore', 'Water (BBLS)'] -= value_to_subtract

value_to_subtract = df.loc[df['Well Name'] == 'JM Moore #192', 'Gas (MCF)'].iloc[0]
df.loc[df['Well Name'] == 'JM Moore', 'Gas (MCF)'] -= value_to_subtract


df.to_csv('data/prod/GC/data.csv',index=False)
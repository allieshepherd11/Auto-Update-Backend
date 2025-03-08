import pandas as pd
from collections import defaultdict
from datetime import datetime
import numpy as np


def c(x):
    if x == x:
        x=x.lower().replace('#', '').replace(' ', '')
    return x

df_tam = pd.read_csv('./data/misc/ST/TAM_update_2025-02-17.csv')
df_stprod= pd.read_excel("C:/Users/plaisancem/CML Exploration/Travis Wadman - CML/STprod.xlsx")

df_stprod['Well Name'] = df_stprod['Well Name'].apply(lambda x: x.lower().replace('#', '').replace(' ', ''))
df_tam['Well Name'] = df_tam['Well Name'].apply(lambda x: c(x))

df_tam['Date'] = pd.to_datetime(df_tam['Date'], format='%m/%d/%Y')
df_tam = df_tam.sort_values('Date').reset_index(drop=True)
df_tam = df_tam.loc[df_tam.groupby('Well Name')['Date'].idxmax()]



sns = []
ds = []
for _,row in df_tam.iterrows():
    mask = row['Well Name'] == df_stprod['Well Name']
    if mask.any():
        stprod_d = df_stprod.loc[mask,'Plunger Diameter (in)'].values[0]
        tam_d = row['Plunger Diameter (in)']
        tam_sn = row['Seating Nipple Depth (ft)']
        stprod_sn = df_stprod.loc[mask,'Pump Depth'].values[0]


        if abs(tam_sn - stprod_sn) > 5:
            print(row['Well Name'])
            print('stprod',stprod_sn)
            print('tam',tam_sn,'\n')
            sns.append([row['Well Name'],f'stprod {stprod_sn}',f'tam {tam_sn}'])

        if tam_d != stprod_d:
            ds.append([row['Well Name'],f'stprod {stprod_d}',f'tam {tam_d}'])

print('SN')
for i in sns:
    print(i)
print('\n Diameters')
for i in ds:
    print(i)

import pandas as pd
import numpy as np
import json
import main

dfiwmain = pd.read_csv('data/prod/IW/data.csv')
print(dfiwmain)
main.updateApp('Inactive Wells',0,0)
exit()
df = pd.read_json('C:/Users/plaisancem/Documents/Dev/Apps/Prod/frontend/data/IW/prodIW.json')
df1 = pd.read_json('data\misc\excludeWells.json')
df2 = pd.read_csv('data/prod/IW/data.csv')
w = df1['ST'].values
ww = np.unique(df2['Well Name'].values)

wells = np.unique(df[0].values)
wells = np.append(wells,w)
wells = np.append(wells,ww)


wells = np.unique(wells)

dfprod = pd.DataFrame()
for i in ['ST','ET','NM','GC','WT','WB','IW']:
    dfprod = pd.concat([dfprod,pd.read_csv(f'data/prod/{i}/data.csv',low_memory=False)])

dfprod = dfprod.drop_duplicates()
print(dfprod)
with open('data/prod/IW/wells.json', 'w') as f:
    json.dump(sorted(wells),f)
dfiw = dfprod.loc[dfprod['Well Name'].isin(wells)]
print(dfiw)
print(pd.read_csv('data/prod/IW/data.csv'))
dfiw.to_csv('data/prod/IW/data.csv',index=False)
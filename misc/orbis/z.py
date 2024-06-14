import pandas as pd
import json


#pd.concat([
#    pd.read_csv('data/prod/ET/data.csv'),
#    pd.read_csv('data/prod/ST/data.csv')
#]).drop_duplicates().to_csv('prodData.csv',index=False)

df = pd.read_csv('misc/orbis/prodData.csv')
df['Date'] = pd.to_datetime(df['Date'])
df = df.sort_values(['Date', 'Well Name'], ascending = [False , True]).reset_index(drop=True)
with open('misc/orbis/orbiswells.json') as f: orbisWells = json.load(f)

dfWells = set(df['Well Name'].str.upper().tolist())
#with open('misc/orbis/dfwells.json','w') as f: orbisWells = json.dump(sorted(dfWells),f)
for well in orbisWells:
    if well not in dfWells:
        print(well)

df['Well Name'] = df['Well Name'].str.upper()
dfOrbis = df[df['Well Name'].isin(orbisWells)]

dfOrbis.to_csv('misc/orbis/orbisProd.csv',index=False)
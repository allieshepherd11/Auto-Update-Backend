import pandas as pd

wells = []
for field in ['ST','ET','NM','GC','WT']:
    df = pd.read_csv(f'data\prod\{field}\data.csv')
    wells.append(sorted(set(df['Well Name'].tolist())))
print(wells)
print(len(wells))
ww = [f.lower() for w in wells for f in w]


dfcuml = pd.read_json('data\prod\ST\cuml.json')
print(dfcuml)
dfcuml = dfcuml.rename(columns={0:'Well Name',1:'Oil Cuml [MBO]',2:'Water Cuml [MBW]',3:'Gas Cuml [MMCF]'})
print(dfcuml)
print(len(dfcuml['Well Name']))

dfapi = pd.read_csv('data\misc\\apinumbers.csv')
dfapi["API14"] = dfapi["API14"].astype(str)
dfapi["API14"] = dfapi['API14'].str[:10]
dfapi['name'] = dfapi['Well Name'].str.cat(dfapi['Well Number'].astype(str), sep=' #')
dfapi = dfapi.drop(['Well Name','Well Number'],axis=1)
dfapi = dfapi.rename(columns={'name':'Well Name'})
dfapi = dfapi.drop_duplicates(subset='Well Name', keep='first').reset_index(drop=True)
dfapi.to_csv('apinums.csv',index=False)
dfapi = dfapi[dfapi['Well Name'].str.lower().isin(dfcuml['Well Name'].str.lower().tolist())].reset_index(drop=True)
print(dfapi)


dfmo = pd.read_csv('data\prod\ST\moData.csv')
dfmo = dfmo[dfmo['Date'] == '2023-08-01'].reset_index(drop=True)


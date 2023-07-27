import pandas as pd

df = pd.read_csv('data\prod\GC\data.csv')
print(df)
df.loc[df['Well Name'] == 'JM MOORE','Well Name'] = 'JM Moore'
print(df)
mask = (df['Well Name'].str.contains("JM Moore"))
print(df[mask])
jms = ['JM Moore 178','JM Moore 192','JM Moore Main Battery','JM Moore Test Battery']

res = {'Well Name':[],'Date':[],'Oil (BBLS)':[],'Gas (MCF)':[],'Water (BBLS)':[],'TP':[],'CP':[],'Comments':[]}
ds = set(df['Date'].tolist()); ds = list(ds)

for d in ds:
    mask = ((df['Well Name'].isin(jms)) & (df['Date'] == d))
    if not mask.any(): continue
    jmdf = df[mask]
    sums = jmdf[['Oil (BBLS)', 'Gas (MCF)','Water (BBLS)']].sum()
    tp = jmdf.loc[jmdf['Well Name'] == 'JM Moore 192', 'TP'].tolist()[0]
    cp = jmdf.loc[jmdf['Well Name'] == 'JM Moore 192', 'CP'].tolist()[0]
    c192 = jmdf.loc[jmdf['Well Name'] == 'JM Moore 192', 'Comments'].tolist()[0]; c178 = jmdf.loc[jmdf['Well Name'] == 'JM Moore 178', 'Comments'].tolist()[0]
    comm192 = c192 if c192 != 'nan' else ''
    comm178 = c178 if c178 != 'nan' else ''
    entry = {'Well Name':'JM Moore','Date':d,'Oil (BBLS)':sums['Oil (BBLS)'],'Gas (MCF)':sums['Gas (MCF)'],
                'Water (BBLS)':sums['Water (BBLS)'],'TP':tp,'CP':cp,'Comments':f'192: {comm192} 178: {comm178}'}
    entry = {k:[v] for k,v in entry.items()}
    df = pd.concat([df,pd.DataFrame(entry)])

df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])
mask = ~df['Well Name'].isin(jms)

df = df[mask]
print(df)
df.to_csv('data\prod\GC\data1.csv',index=False)
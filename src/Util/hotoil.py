import pandas as pd

df = pd.read_csv('data/prod/ST/data.csv')
print(df)
df['Date'] = pd.to_datetime(df['Date'])
df['Fluid'] = df['Oil (BBLS)']  + df['Water (BBLS)']

mask = df['Comments'].str.contains('hot oil|hot water|ho ',case=False,na=False)
dfHo = df.loc[mask][['Well Name','Date','Comments']]
df['Month Prior'] = None
df['Month After'] = None
df['Week After'] = None

l=len(dfHo)
for idx,row in dfHo.copy().reset_index(drop=True).iterrows():
    print(l-idx)
    after1 = (df['Date'] < row['Date'] + pd.DateOffset(months=1)) & (df['Date'] >= row['Date'])
    afterW1 = (df['Date'] < row['Date'] + pd.DateOffset(weeks=1)) & (df['Date'] >= row['Date'])
    prior1 = (df['Date'] > row['Date'] - pd.DateOffset(months=1)) & (df['Date'] < row['Date'])

    dfwell = df.loc[df['Well Name'] == row['Well Name']]
    mask = (dfHo['Well Name'] == row['Well Name']) & (dfHo['Date'] == row['Date'])
    dfHo.loc[mask,['Month Prior','Week After','Month After']] = dfwell.loc[prior1]['Fluid'].mean(), \
        dfwell.loc[afterW1]['Fluid'].mean(),dfwell.loc[after1]['Fluid'].mean()
dfHo.to_excel('data/misc/hoJune.xlsx',index=False)
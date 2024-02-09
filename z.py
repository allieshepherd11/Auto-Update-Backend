import pandas as pd

df=pd.read_csv('data/prod/ET/data.csv')
ruen2 = df.loc[df['Well Name'] == 'Ruen #2']
ruen2 = ruen2.iloc[::-1]
ruen2['Fluid'] = ruen2['Oil (BBLS)'] + ruen2['Water (BBLS)']
ruen2['Date'] = pd.to_datetime(ruen2['Date'],format='%Y-%m-%d')
ruen2 = ruen2.groupby(ruen2['Date'].dt.to_period('M'))['Oil (BBLS)'].sum()
print(ruen2)
ruen2.to_excel('ruen2.xlsx')
import pandas as pd

df = pd.read_csv('data/prod/NM/data.csv')
print(df)
mask = (df['Date'] == '2023-08-23') 
print(df[mask])

#df.loc[(df['Well Name'] == 'Abenaki 10 State #2') & (mask) ,['Oil (BBLS)','Gas (MCF)','Water (BBLS)']] = 8.4,19,0
#df.loc[(df['Well Name'] == 'Abenaki 10 State #3') & (mask) ,['Oil (BBLS)','Gas (MCF)','Water (BBLS)']] = 5.6,30,0
#
#df.loc[(df['Well Name'] == 'Beams 15 State #2') & (mask) ,['Oil (BBLS)','Gas (MCF)','Water (BBLS)']] = 5.6,21,0
#df.loc[(df['Well Name'] == 'Beams 15 State #4') & (mask) ,['Oil (BBLS)','Gas (MCF)','Water (BBLS)']] = 0,0,0
#
#df.loc[(df['Well Name'] == 'Henry 24 #1') & (mask) ,['Oil (BBLS)','Gas (MCF)','Water (BBLS)']] = 2.8,0,11
#df.loc[(df['Well Name'] == 'Henry 24 #2') & (mask) ,['Oil (BBLS)','Gas (MCF)','Water (BBLS)']] = 2.8,0,11

df.loc[(df['Well Name'] == 'Paddy 15 State #1') & (mask) ,['Oil (BBLS)','Gas (MCF)','Water (BBLS)']] = 5.3,3.1,56.7 
df.loc[(df['Well Name'] == 'Paddy 15 State #2') & (mask) ,['Oil (BBLS)','Gas (MCF)','Water (BBLS)']] = 9.5,9.9,1.8
df.loc[(df['Well Name'] == 'Paddy 15 State #3') & (mask) ,['Oil (BBLS)','Gas (MCF)','Water (BBLS)']] = 2.8,0,10

#df.loc[(df['Well Name'] == 'Paddy 18 State #1') & (mask) ,['Oil (BBLS)','Gas (MCF)','Water (BBLS)']] = 2.8,6,45
#df.loc[(df['Well Name'] == 'Paddy 18 State #3') & (mask) ,['Oil (BBLS)','Gas (MCF)','Water (BBLS)']] = 2.8,6,129.6

df.loc[(df['Well Name'] == 'Paddy 19 State #1') & (mask) ,['Oil (BBLS)','Gas (MCF)','Water (BBLS)']] = 0,0,0
df.loc[(df['Well Name'] == 'Paddy 19 State #4') & (mask) ,['Oil (BBLS)','Gas (MCF)','Water (BBLS)']] = 0,0,18.5
df.loc[(df['Well Name'] == 'Paddy 19 State #5') & (mask) ,['Oil (BBLS)','Gas (MCF)','Water (BBLS)']] = 2.8,1,20

#df.loc[(df['Well Name'] == 'Paddy 19 State #2') & (mask) ,['Oil (BBLS)','Gas (MCF)','Water (BBLS)']] = 3.4,3,60
#df.loc[(df['Well Name'] == 'Paddy 19 State #3') & (mask) ,['Oil (BBLS)','Gas (MCF)','Water (BBLS)']] = 3.3,4,158
#
#df.loc[(df['Well Name'] == 'Raider 9 St #1') & (mask) ,['Oil (BBLS)','Gas (MCF)','Water (BBLS)']] = 19.6,119,0
#df.loc[(df['Well Name'] == 'Raider 9 St #3') & (mask) ,['Oil (BBLS)','Gas (MCF)','Water (BBLS)']] = 16.7,77,0



df.to_csv('data/prod/NM/data.csv',index=False)

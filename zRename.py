import pandas as pd
import plotly.graph_objects as go
import datetime
def gc():
    df = pd.read_excel('Gulf Coast Production 2002-01-01 to 2023-07-20.xlsx')
    print(df)
    df = df.drop(['Dateold'],axis=1)
    df = df.rename(columns={'Well': 'Well Name','Oil':'Oil (BBLS)','Gas':'Gas (MCF)','Water':'Water (BBLS)','FTP':'TP'})
    #df = df[df['Dateold'] == '2023-06-23']
    print(df)
    df.to_csv('data\prod\GC\data.csv',index=False)


def wt():
    df = pd.read_excel('New Mexico Production 2004-01-01 to 2023-07-24.xlsx')
    print(df[df['Date'] == '2023-06-23'])
    print(df)
    df = df.drop(['Dateold'],axis=1)
    df = df.rename(columns={'Well': 'Well Name','Oil':'Oil (BBLS)','Gas':'Gas (MCF)','Water':'Water (BBLS)','FTP':'TP'})
    #df = df[df['Dateold'] == '2023-06-23']
    df = df[:99169]
    df.to_csv('data\\prod\\NM\\data.csv',index=False)
    return


df = pd.read_csv('data\prod\WT\data.csv')
print(df[:20])

df.loc[df['Well Name'] == 'BROTHERS HORIZON UNIT','Well Name'] = 'Brothers Horizon Unit 1'
df.loc[df['Well Name'] == 'BROTHERS HORIZON','Well Name'] = 'Brothers Horizon'


df.loc[df['Well Name'] == 'MULESHOE RANCH #1','Well Name'] = 'Muleshoe Ranch #1'

df.loc[df['Well Name'] == 'BECK UNIT #1','Well Name'] = 'Beck Unit #1'

df.loc[df['Well Name'] == "KOONSMAN '677'",'Well Name'] = 'Koonsman 677'

df.loc[df['Well Name'] == "EVERETT UNIT #1",'Well Name'] = 'Everett Unit #1'

df.loc[df['Well Name'] == "BRUMLEY LEASE",'Well Name'] = 'Brumley'

df.loc[df['Well Name'] == "EDWARDS '12' #1",'Well Name'] = 'Edwards 12 #1'
df.loc[df['Well Name'] == "BLAIR-TXL #3",'Well Name'] = 'Blair TXL 7 #3'
df.loc[df['Well Name'] == "BLAIR-TXL #1",'Well Name'] = 'Blair TXL 7 #1'

df.loc[df['Well Name'] == "SOUTH JOHN",'Well Name'] = 'South JUMF'
df.loc[df['Well Name'] == "NORTH JOHN",'Well Name'] = 'North JUMF'

df.loc[df['Well Name'] == "SLAUGHTER B",'Well Name'] = 'Slaughter B'
df.loc[df['Well Name'] == "LLB '15' #1",'Well Name'] = 'LLB 15 #1'

df.loc[df['Well Name'] == "BULLARD #5-#9",'Well Name'] = 'Bullard'
df.loc[df['Well Name'] == "Davis 3",'Well Name'] = 'Davis Lease'








df.to_csv('z.csv',index=False)
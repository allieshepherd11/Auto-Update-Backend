import pandas as pd
from datetime import datetime, timedelta
df = pd.read_csv('data/prod/ST/data.csv')
df['Well Name'] = df['Well Name'].str.title()

def ho(well,date):
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    past14 = int((date_obj - timedelta(days=14)).timestamp())
    next14 = int((date_obj + timedelta(days=14)).timestamp())
    p14 = datetime.fromtimestamp(past14).strftime('%Y-%m-%d')
    n14 = datetime.fromtimestamp(next14).strftime('%Y-%m-%d')

    mask = (df['Well Name'] == well) & (df['Date'] >= p14) & (df['Date'] < date)
    m = (df['Well Name'] == well) & (df['Date'] <= n14) & (df['Date'] > date)
    if not mask.any():print(f'NOT FOUND {well}');exit()
    if not m.any():
        print(date)
        print(f'NOT FOUND {well}');exit()

    dfp14 = df[mask]
    dfn14 = df[m]

    pastAvg = dfp14['Oil (BBLS)'].sum()/len(dfp14)
    print(dfn14)
    currAvg = dfn14['Oil (BBLS)'].sum()/len(dfn14)
    
    return pastAvg,currAvg,currAvg - pastAvg

def handle(day):
    if len(str(day)) == 1: day = f'0{day}'
    return f'2023-08-{day}'
dfho = pd.read_csv('misc\HO\\ho.csv')
dfho['Date'] = dfho['Date'].apply(lambda day: handle(day))
wells:dict = dfho.to_dict(orient='records')
print(wells)
res = {'well':[],'response':[]}
for well in wells:
    avg = ho(well['Well'],well['Date'])
    res['well'].append(well['Well']);res['response'].append(avg[2])

pd.DataFrame(res).to_excel('hoResponse1.xlsx',index=False)
pd.DataFrame(res).to_csv('hoResponse.csv',index=False)


import pandas as pd
import json
from datetime import datetime


df=pd.read_csv('runticketsCurr.csv')
print(df)
df=df.drop(['updated_at'],axis=1)
df['date_string'] = pd.to_datetime(df['date_string'],format="%Y-%m-%d")
df = df.sort_values(['date_string', 'well'], ascending = [False , True]).reset_index(drop=True)

data = df.to_dict(orient='records')
#.to_json('../frontend\data\ST/analyzeST.json',orient='records')
res = {}
for ticket in data: 
    well = ticket['well']
    d = {
            'id':ticket['id'],
            'date':datetime.strptime(ticket['date_string'].strftime('%Y-%m-%d %H:%M:%S'), "%Y-%m-%d %H:%M:%S").strftime('%m-%d-%y'),
            'type':ticket['type'],
            'total':ticket['total']
        }
    if well not in res:
        res[well] = [d]
    else: res[well].append(d)
with open('../frontend\data\ST/runtickets.json','w') as f: json.dump(res,f)

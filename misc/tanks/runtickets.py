import pandas as pd
import json
from datetime import datetime


with open('data/prod/ST/runticketsSet.json','r') as f: data = json.load(f)

print(data)

df = {'well':[],'id':[],'run_ticket_number':[],'unix':[],'date':[],'updated_at':[],'type':[],'total':[]}

for well,tickets in data.items():
    for ticket in tickets:
        df['well'].append(well)
        df['id'].append(ticket['id'])
        df['unix'].append(ticket['date'])
        df['type'].append(ticket['type'])
        df['total'].append(ticket['total'])
        df['run_ticket_number'].append(ticket['run_ticket_number'])
        df['date'].append(datetime.utcfromtimestamp(ticket['date']).strftime("%Y-%m-%d"))
        df['updated_at'].append(ticket['date'])


df = pd.DataFrame(df)
df = df.sort_values(['well', 'date'], ascending = [True , False])
df.to_csv('data/prod/ST/runtickets.csv',index=False)
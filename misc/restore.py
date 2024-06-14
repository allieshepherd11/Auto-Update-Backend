import pandas as pd
from datetime import datetime

df = pd.read_json('C:/Users/plaisancem/Documents/Dev/Apps/Prod/frontend/data/ST/prodST.json')
colNames = ["Well Name", "Date", "Oil (BBLS)","Gas (MCF)", "Water (BBLS)", "TP", "CP", "Comments","DateYAxis","Total Fluid","7DMA Oil","7DMA Fluid","30DMA Oil"]

df = df.rename(columns={idx:name for idx,name in enumerate(colNames)})
keep = ['Well Name','Date','Oil (BBLS)','Gas (MCF)','Water (BBLS)','TP','CP','Comments']
df['Date'] = df['Date'].apply(lambda x: datetime.strptime(x, "%B %d, %Y").strftime("%Y-%m-%d"))

df.drop([col for col in df.columns if col not in keep],axis=1).to_csv('data/prod/st/data.csv',index=False)

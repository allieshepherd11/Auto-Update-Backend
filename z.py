import pandas as pd
from collections import defaultdict
import json


df = pd.read_csv(r"C:\Users\plaisancem\Documents\Dev\Apps\Prod\backend\data\misc\ST\TAM Pump Info All.csv")

print(df.columns)

df['Date'] = pd.to_datetime(df['Date'])

latest_idx = (
    df[df['Strokes Per Minute (SPM)'].notna()]          # ignore rows with null in col a
      .groupby('Well Name')['Date']       # per name, look only at the date column
      .idxmax()                      # index of the max (most-recent) date
)

result = df.loc[latest_idx].reset_index(drop=True)


result = result[['Well Name','Pump Run Date','Date','Seating Nipple Depth (ft)','Plunger Diameter (in)']]
print(result)
result.to_excel('TAM Pump Info Recent.xlsx',index=False)
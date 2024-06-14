import pandas as pd 


df = pd.read_csv("C:/Users/plaisancem/CML Exploration/Travis Wadman - CML/East Texas/ET Fluid Levels.csv")
df['datetime'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
print(df)
df = df.fillna(0)
df = df[df['Gas Free Above Pump (ft)'].notna()]
df = df.loc[df.groupby('Well Name')['datetime'].idxmax()].reset_index(drop=True)
print(df)
df.to_csv("C:/Users/plaisancem/CML Exploration/Travis Wadman - CML/East Texas/ET Fluid Levels1.csv",index=False)
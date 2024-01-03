import pandas as pd
from datetime import datetime
import re
import numpy as np


#df['7DMA'] = df.groupby('Well Name')['Oil (BBLS)'].transform(lambda x: x.rolling(window=7, min_periods=1).mean())
#df_schedule = pd.read_excel(f'C:/Users/plaisancem/OneDrive - CML Exploration/CML/South Texas/{2023-12} OnOff Schedule.xlsx')
#pd.set_option('display.max_columns',None)
pd.set_option('display.max_rows',None)

def parse_schedule(df_prod:pd.DataFrame) -> list:
    #df_prod = df_prod[df_prod['Total Fluid'] != 0].sort_values(by='Datetime',ascending=False).reset_index(drop=True)
    #df_prod = df_prod.groupby('Well Name').first().drop([col for col in df_prod.columns if col not in ['Well Name', 'Date']],axis=1)
    #df_prod['Date'] = pd.to_datetime(df_prod['Date'])
    #df_prod['Days Since Prod'] = (datetime.now() - df_prod['Date']).dt.days - 1

    curr_mnth = datetime.now().strftime("%Y-%m")
    df = pd.read_excel(f'C:/Users/plaisancem/OneDrive - CML Exploration/CML/South Texas/{curr_mnth} OnOff Schedule.xlsx').iloc[:,:2]
    df = df.rename(columns={el:idx for idx,el in enumerate(df.columns)})
    shutins = df.loc[df[1].str.contains("shut",case=False)][0].tolist()
    df = df[((df[1].str.contains("on",case=False)) & (df[1].str.contains("off",case=False)))]

    df['On'] = df[1].str.extract(r'(\d+)\s+on',flags=re.IGNORECASE)
    df['Off'] = df[1].str.extract(r'(\d+)\s+off',flags=re.IGNORECASE)
    #df = df.rename(columns={0:'Well Name'})
    #df = pd.merge(df,df_prod,on='Well Name',how='left').drop([1,'Date'],axis=1)
   
    return shutins + df[0].tolist()
    
def analyze(field):
    df = pd.read_json(f'data/prod/{field}/data.json')
    cols = ["Well Name", "Date", "Oil (BBLS)","Gas (MCF)", "Water (BBLS)", "TP", "CP", "Comments","Datetime","Total Fluid","7DMA Oil","7DMA Fluid","30DMA Oil"]
    df = df.rename(columns={idx:el for idx,el in enumerate(cols)})
    recent_date = df.sort_values('Datetime', ascending=False)['Datetime'].tolist()[0]
    
    #df['MA Ratio Oil'] = df['7DMA Oil'] / df['30DMA Oil']
    df['MA Ratio Oil'] = np.where(df['30DMA Oil'] != 0, df['7DMA Oil'] / df['30DMA Oil'], 1)

    exclude = parse_schedule(df)
    conditions = {
        'Low MA Oil': (df["MA Ratio Oil"] < .8),
        'No Fluids': (df['Total Fluid'] == 0) & ~(df['Well Name'].isin(exclude)),
        'No Oil': (df['Oil (BBLS)'] == 0) & ~(df['Well Name'].isin(exclude)),
    }
    
    mask = ((conditions["Low MA Oil"] | conditions["No Fluids"] | conditions['No Oil']) & ~(df['30DMA Oil'] == 0))
    df_analysis = df.loc[df['Datetime'] == recent_date].loc[mask]
    
    for case,condition in conditions.items():
        df_analysis[case] = condition

    df_analysis['case'] = df_analysis \
                    .apply(lambda row: [condition for condition in conditions.keys() if row[condition]], axis=1)
    
    return df_analysis.drop(conditions.keys(),axis=1)

df=analyze('ST')
print(df.columns)
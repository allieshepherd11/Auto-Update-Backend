import pandas as pd,numpy as np
import datetime

def main(field:str):
    apinums = pd.read_csv(f'misc/archgis/apinums{field.lower()}.csv')
    dfmo = pd.read_csv(f'data\prod\{field}\moData.csv')
    dfcuml = pd.read_json(f'data\prod\{field}\cuml.json')#wn,o,w,g
    dfforms = pd.read_excel('data/misc/formations.xlsx')
    df = pd.read_csv(f'data\prod\{field}\data.csv')
    
    dfcuml = dfcuml.rename(columns={0:'Well Name',1:'Oil [MBO]',3:'Gas [MMCF]'})
    print(dfcuml)
    df['Well Name'] = df['Well Name'].str.upper()
    dfmo['Well Name'] = dfmo['Well Name'].str.upper()

    dfforms['Well Name'] = dfforms['Well Name'].str.upper()
    dfcuml['Well Name'] = dfcuml['Well Name'].str.upper()
    dfmo['Well Name'] = dfmo['Well Name'].str.upper()
    
    df['Date'] = pd.to_datetime(df['Date'])
    firstprod = df.copy().groupby('Well Name')['Date'].idxmin()
    dff = df.loc[firstprod].reset_index(drop=True)

    dfmo = dfmo[dfmo['Date'] == '2023-08-01']
    dfmo = dfmo.rename(columns={'Oil (BBLS)': 'Aug Oil [BBLS]','Gas (MCF)': 'Aug Gas [MCF]'})
    
    apinums = apinums.merge(dfmo[['Well Name','Aug Oil [BBLS]','Aug Gas [MCF]']], on='Well Name', how='left')
    apinums = apinums.merge(dff[['Well Name','Date']], on='Well Name', how='left')
    apinums = apinums.merge(dfforms[['Well Name','Formation']], on='Well Name', how='left')
    apinums = apinums.merge(dfcuml[['Well Name','Oil [MBO]','Gas [MMCF]']], on='Well Name', how='left')
    pd.set_option('display.max_columns',None)
    apinums['Active'] = True
    apinums.loc[(apinums['Aug Oil [BBLS]'].isin([0, np.nan])) & (apinums['Aug Gas [MCF]'].isin([0, np.nan])), 'Active'] = False
    apinums['EUR'] = None
    apinums = apinums[['Well Name','Formation', 'API14','Well  Number', 'EUR','Oil [MBO]', 'Gas [MMCF]','Aug Oil [BBLS]', 'Aug Gas [MCF]',
       'Date', 'Active']]
    print(apinums)
    apinums.rename(columns={'Date':'Date First Production'}).to_csv('misc/archgis/finalST.csv',index=False)

    
main('ST')
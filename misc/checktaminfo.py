import pandas as pd
import openpyxl

path = "C:/Users/plaisancem/Downloads/stpumpinfo.csv"
df = pd.read_csv(path)
df = df[(~df['Strokes Per Minute (SPM)'].isna())].reset_index(drop=True)
df['Date'] = pd.to_datetime(df['Date'] + ' ' + df['Time'],format='mixed')


dfrecent = df.loc[df.groupby('Well Name')['Date'].idxmax()]

file_path = "C:/Users/plaisancem/CML Exploration/Travis Wadman - CML/STprod.xlsx"
wb = openpyxl.load_workbook(file_path)
sheet = wb['Prod']  

dfstprod = pd.read_excel(file_path)
dfstprod['Key'] = dfstprod['Well Name'].apply(lambda x: x.lower().replace('#', '').replace(' ', ''))

for _, row in dfrecent.iterrows():
    row_key = row['Well Name'].lower().replace('#', '').replace(' ', '')
    mask = row_key == dfstprod['Key']
    if mask.any():
        pDia = dfstprod.loc[mask,'Diam Plunger (in)'].tolist()[0]
        sn = dfstprod.loc[mask,'Pump Depth'].tolist()[0]
        if abs(row['Seating Nipple Depth (ft)'] - sn) > 5:
            print(row['Well Name'],'TAM',row['Seating Nipple Depth (ft)'],'STprod',sn,'\n')
        if row['Plunger Diameter (in)'] != pDia:
            print(row['Well Name'],'TAM',row['Plunger Diameter (in)'],'STprod',pDia,'\n')
    else:
        print('No Match',row['Well Name'],'\n')
import pandas as pd
import openpyxl

dfimport = pd.read_csv('./data/misc/ST/fl_import_10-17.csv')

df = pd.read_csv('./data/misc/ST/fls.csv')
df = pd.concat([df,dfimport]).reset_index(drop=True)
df.to_csv('fls.csv',index=False)

df = df[(~df['Distance to Liquid (ft)'].isna()) & (df['Well State'] == 'Producing')].reset_index(drop=True)
df['Date'] = pd.to_datetime(df['Date'] + ' ' + df['Time'],format='mixed')

df.to_json(f'../frontend/data/ST/fls.json', orient='values', date_format='iso')

dfrecent = df.loc[df.groupby('Well Name')['Date'].idxmax()]

# Load the Excel file with openpyxl to preserve formatting
file_path = "C:/Users/plaisancem/CML Exploration/Travis Wadman - CML/STprod.xlsx"
wb = openpyxl.load_workbook(file_path)
sheet = wb.active  # or wb['SheetName'] if needed

# Load the Excel file into a dataframe to handle the data easily
dfstprod = pd.read_excel(file_path)
dfstprod['Key'] = dfstprod['Well Name'].apply(lambda x: x.lower().replace('#', '').replace(' ', ''))

for _, row in dfrecent.iterrows():
    row_key = row['Well Name'].lower().replace('#', '').replace(' ', '')
    mask = row_key == dfstprod['Key']
    #if not mask.any():
    #    print(row['Well Name'])
    dfstprod.loc[mask, ['FL Date', 'GFLAP']] = row['Date'], row['Gas Free Above Pump (ft)']

dfstprod['FL Date'] = pd.to_datetime(dfstprod['FL Date']).dt.date

# Write the modified dataframe back to the workbook, while preserving the original formatting
for idx, row in dfstprod.iterrows():
    well_name_col = 'A'  # Column for 'Well Name'
    fl_date_col = 'K'    # Column for 'FL Date'
    gflap_col = 'L'      # Column for 'GFLAP'

    well_name_cell = sheet[f'{well_name_col}{idx + 2}']  # Header row
    fl_date_cell = sheet[f'{fl_date_col}{idx + 2}']
    gflap_cell = sheet[f'{gflap_col}{idx + 2}']

    if well_name_cell.value == row['Well Name']:
        fl_date_cell.value = row['FL Date']
        gflap_cell.value = row['GFLAP']

wb.save('stprodupdated.xlsx')

import pandas as pd

def create_key_col(df:pd.DataFrame):
    df['Well Key'] = df['Well Name'].str.lower()
    df['Well Key'] = df['Well Key'].str.replace('#', '', regex=False)
    df['Well Key'] = df['Well Key'].str.replace(' ', '', regex=False)
    df['Well Key'] = df['Well Key'].str.replace('-', '', regex=False)
    df['Well Key'] = df['Well Key'].str.replace('unit', '', regex=False)
    return df

df = pd.read_csv('ptn_summary.csv')
df_jrr = pd.read_csv("roe.csv")

df_jrr = create_key_col(df_jrr)
df_ptn = create_key_col(df)

wells_jrr = df_jrr['Well Key'].tolist()
wells_ptn = df_ptn['Well Key'].tolist()

df_manual = pd.read_csv('missed PTN.csv')
df_manual = df_manual.fillna('')
df_jrr['PTN Well Name'] = ''

for well_key_jrr in wells_jrr:
    if well_key_jrr in wells_ptn:
        ptn_well_name = df_ptn.loc[df_ptn['Well Key'] == well_key_jrr,'Well Name'].tolist()[0]
        df_jrr.loc[df_jrr['Well Key'] == well_key_jrr,'PTN Well Name'] = ptn_well_name

for _,row in df_manual.iterrows():
    if row['Well Name Jrr'] != '':
        ptn_well_name = df_ptn.loc[df_ptn['Well Key'] == row['Missed PTN Well Key'],'Well Name'].tolist()[0]
        df_jrr.loc[df_jrr['Well Name'] == row['Well Name Jrr'],'PTN Well Name'] = ptn_well_name



  
df_jrr.to_csv('JRR Interest.csv',index=False)
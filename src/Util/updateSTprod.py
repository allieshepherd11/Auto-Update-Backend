import pandas as pd


if __name__ == '__main__':
    pd.set_option('display.max_columns',None)

    df = pd.read_csv('data/misc/tam.csv')
    df['datetime'] = pd.to_datetime(df['Date'] + " " + df['Time'])
    df_sorted = df.sort_values(by=['Well Name', 'datetime'], ascending=[True, False])
    df_filled = df_sorted.groupby('Well Name').apply(lambda group: group.ffill().bfill())
    df_recent = df_filled.drop_duplicates(subset='Well Name', keep='first')
    df_recent.reset_index(drop=True, inplace=True)

    dfprod = pd.read_excel("C:/Users/plaisancem/CML Exploration/Travis Wadman - CML/STprod - Copy.xlsx")

    for _,row in df_recent.iterrows():
        mask = dfprod['Well Name'].str.replace(' ', '').str.lower() == row['Well Name'].replace(' ', '').lower()
        if mask.any():
            if pd.notna(row['Strokes Per Minute (SPM)']):
                dfprod.loc[mask, 'SPM'] = row['Strokes Per Minute (SPM)']

            if pd.notna(row['Maximum Plunger Stroke (in)']):
                dfprod.loc[mask, 'DH SL'] = row['Maximum Plunger Stroke (in)']

            if pd.notna(row['Effective Plunger Travel (in)']):
                dfprod.loc[mask, 'EPT'] = row['Effective Plunger Travel (in)']

            if pd.notna(row['Date']):
                dfprod.loc[mask, 'FL Date'] = row['Date']

            if pd.notna(row['Gas Free Above Pump (ft)']):
                dfprod.loc[mask, 'GFLAP'] = row['Gas Free Above Pump (ft)']

            prodsn = dfprod.loc[mask,'Pump Depth'].tolist()[0]
            tamsn = row['Seating Nipple Depth (ft)']
            if abs(prodsn - tamsn) > 10:
                print(f'{row['Well Name']}\nProd SN {prodsn}\nTAM SN {tamsn}\n')
        else:
            pass
            #print('missed',row['Well Name'])

    #dfprod.to_csv('data/misc/stProdImport.csv',index=False)
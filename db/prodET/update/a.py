import pandas as pd

def main(field):#ET / ST
    dtype = {'Oil (BBLS)': float, 'Water (BBLS)': float, 'Gas (MCF)': float, 'TP': str, 'CP': str, 'Comments': str}
    df = pd.read_csv(f'db\\prodET\\update\\dataET.csv', dtype=dtype)
    #df = pd.read_json('data.json')
    df = df.fillna('')
    df.Date = pd.to_datetime(df.Date)
    df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])
    start = df.iloc[0]['Date'].date() # Gets the most recent date from the dataframe

    
    print("\ndf:\n",df)
    df['Gas (MCF)'] = pd.to_numeric(df['Gas (MCF)'])
    df.reset_index(drop=True, inplace=True)

    # Fix blanks and clip negative values
    df['Oil (BBLS)'].replace('',0, inplace=True)
    df['Water (BBLS)'].replace('',0, inplace=True)
    df['Gas (MCF)'].replace('',0, inplace=True)
    df['Oil (BBLS)'] = df['Oil (BBLS)'].clip(lower=0).round()
    df['Water (BBLS)'] = df['Water (BBLS)'].clip(lower=0).round()
    df['Gas (MCF)'] = df['Gas (MCF)'].clip(lower=0).round()
    df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])
    
    #Add total fluid column
    #df['Total Fluid'] = df['Oil (BBLS)'] + df['Water (BBLS)']

    # Save to original data file
    df.to_json(f'db\\prod{field}\\update\\data{field}.json')
    df.to_csv(f'db\\prod{field}\\update\\data{field}.csv', index=False)
    

    # Get 30 day moving average and append column to df
    df = df.sort_values(['Date', 'Well Name'], ascending = [True , True])
    if field == "ST": 
        df['7DMA'] = df.groupby('Well Name')['Oil (BBLS)'].transform(lambda x: x.rolling(7, 1).mean().round(1))
        df['30DMA'] = df.groupby('Well Name')['Oil (BBLS)'].transform(lambda x: x.rolling(30, 1).mean().round(1))
        df['MA Ratio'] = df['7DMA']/df['30DMA']
        df['MA Ratio'] = df['MA Ratio'].round(2)
        df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])
        ##analyze(df)
        df.drop(['30DMA', 'MA Ratio'], inplace=True, axis = 1)
    
    
    dfoil = df.groupby(['Well Name'])['Oil (BBLS)'].sum().divide(1000).astype(float).reset_index().round(1)
    dfwater = df.groupby(['Well Name'])['Water (BBLS)'].sum().divide(1000).astype(float).reset_index().round(1)
    dfgas = df.groupby(['Well Name'])['Gas (MCF)'].sum().divide(1000).astype(int).reset_index()
    
  
    #df_formations = get_formations()

    dfsum = dfoil.merge(dfwater, on='Well Name').merge(dfgas, on='Well Name')#.merge(df_formations, on='Well Name')
    
    # Create entries for total field production in a way that can integrate with graph
    dfoiltotal = df.groupby(['Date'])['Oil (BBLS)'].sum().astype(int).reset_index()
    dfwatertotal = df.groupby(['Date'])['Water (BBLS)'].sum().astype(int).reset_index()
    dfgastotal = df.groupby(['Date'])['Gas (MCF)'].sum().astype(int).reset_index()

    dfsummary = dfoiltotal.merge(dfwatertotal, on='Date').merge(dfgastotal, on='Date')
    
    title = 'South Texas Total'
    if field == "ET": title = "East Texas Total"
    dfsummary['Well Name'] = title
    
    dfwebsite = pd.concat([df, dfsummary])
    dfwebsite = dfwebsite.sort_values(['Date', 'Well Name'], ascending = [False , True])
    
    
    # CREATING A DF SPECIFIC TO JSON FORMAT (DATETIME)
    df_to_json_format = dfwebsite

    # ADD DATE COLUMN FOR X AXIS USE (DateYAxis) & CHANGING DATATYPE TO Object
    df_to_json_format['DateYAxis'] =  df_to_json_format['Date']
    df_to_json_format['DateYAxis'] =  pd.to_datetime(df_to_json_format['Date'])

    #CHANGING DATE TO OBJECT TYPE AND SPELL OUT FORMAT
    df_to_json_format['Date'] =  pd.to_datetime(df_to_json_format['Date'])
    #df_to_json_format['Date'] = df_to_json_format['Date'].dt.strftime('%Y-%m-%d')
    df_to_json_format['Date'] = df_to_json_format['Date'].dt.strftime('%B %d, %Y')
    
    #add new total fluid col, needs to last col in df to mess up js for website, or add after gas col and change graph.js to point to new indexes 
    dfwebsite['Total Fluid'] = df['Oil (BBLS)'] + df['Water (BBLS)']
    
    

    # SAVING ALL PRODUCTION DATA TO WEBSITE FOLDER
    ##df_to_json_format.to_json("../STprodWebsite/STprod/static/allProductionData.json", orient='values', date_format='iso')
    
    # SAVING ALL PRODUCTION DATA TO WEBSITE FOLDER
    #dfsum.to_json("../STprodWebsite/STprod/static/cumProd.json", orient='values')
    
    #df_info = pd.read_excel('../CML/STprod.xlsx', sheet_name = 'Prod', usecols= 'A,I:R')
    # SAVE & UPLOAD TO AWS WEBSITE
    if field == "ET": 
        dfsum = addFormations(dfsum)
        df_to_json_format = df_to_json_format[["Well Name", "Date", "Oil (BBLS)","Gas (MCF)", "Water (BBLS)", "TP", "CP", "Comments","Total Fluid", "DateYAxis"]]
    print(f'df_to_json_format {df_to_json_format}')
    df_to_json_format.to_json(f"db\\prod{field}\\update\\allProductionData.json", orient='values', date_format='iso') #updating loc json file
    dfsum.to_json(f"db\\prod{field}\\update\\cumProd.json", orient='values', date_format='iso')
    #df_formations.to_json("db\\prodST\\formations.json", orient='values', date_format='iso')
    #df_info.to_json("pumpinfo.json", orient='values', date_format='iso')

def addFormations(df):
    print(f'dfsum: {df}')
    df_forms = pd.read_json('db\\prodET\\formations.json')
    df_forms = df_forms.rename(columns={0:"Well Name", 1 : "Formation"})
    print(f'df form : {df_forms}')

    res = df.merge(df_forms,on="Well Name")
    return res
main("ET")
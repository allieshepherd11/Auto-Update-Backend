import pandas as pd
import glob

def main():
    # Read the main database csv
    dtype = {'Oil (BBLS)': float, 'Water (BBLS)': float, 'Gas (MCF)': float, 'TP': float, 'CP': float, 'Comments': str}
    df = pd.read_csv("data.csv", dtype=dtype, thousands=',')
    df.Date = pd.to_datetime(df.Date)

    # Read the daily production file
    file = glob.glob('custom-report-cml*')[0]
    dfImport = pd.read_csv(file, dtype=dtype, thousands=',', decimal='.')
    dfImport.Date = pd.to_datetime(dfImport.Date)

    # Concat the dataframes
    df = pd.concat([df, dfImport], ignore_index=True)

    # Clean data
    # df = df.fillna('')
    df['Gas (MCF)'] = pd.to_numeric(df['Gas (MCF)'])
    df = df.drop_duplicates()
    df = df.sort_values(['Date', 'Well Name'], ascending = [False , True])

    # Create daily field total production dataframe
    dfsummary = df.groupby(['Date']).agg({'Oil (BBLS)':'sum', 'Water (BBLS)':'sum', 'Gas (MCF)':'sum'}).reset_index()
    dfsummary['Well Name'] = 'South Texas Total'

    # Concat daily field total to existing production data and drop index
    dfwebsite = pd.concat([df, dfsummary]).sort_values(['Date', 'Well Name'], ascending = [False , True]).reset_index(drop=True)
    dfwebsite = dfwebsite.fillna('')
    dfwebsite = dfwebsite.drop_duplicates()
    print(dfwebsite)

    # Calculate the cumulative production for each well
    df[['Oil (BBLS)','Water (BBLS)','Gas (MCF)']] = df[['Oil (BBLS)','Water (BBLS)','Gas (MCF)']].fillna(0)
    df['Oil (BBLS)'] = df['Oil (BBLS)'].round()
    df[['Water (BBLS)','Gas (MCF)']] = df[['Water (BBLS)','Gas (MCF)']].clip(lower=0).round() 

    dfsum = df.groupby(['Well Name']).agg({'Oil (BBLS)':'sum', 'Water (BBLS)':'sum', 'Gas (MCF)':'sum'}).divide(1000).round(1).reset_index()

    print(dfsum)
main()

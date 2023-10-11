# Only run once each month when P&L and payouts excel files are updated in the Database folder. This program should output a P&L file and a payouts file to the ST website folder.
# Change Total column in P&L to read "South Texas Total"
# Make sure well names match website format
import pandas as pd
pd.options.display.float_format = '{:.10f}'.format
drop_index = None

    
def main():
    # pd.options.display.float_format = '${:,.2f}'.format

    # Change usecols to update to current month
    df = pd.read_excel('2023_P&L.xlsx', usecols='B,I:L')
    df_pl = df.copy()
    df_pl['YTD P&L'] = 0
    # months = ['Jan', 'Feb', 'Mar', 'April', 'May', 'Jun']

    # Generalize the code to handle whatever date range is selected when reading the csv
    effective_dates = range(1, df_pl.shape[1]-1)
    for i in effective_dates:
        df_pl['YTD P&L'] += df_pl.iloc[:, i]
              
    # Drop the P&L columns except for the the most recent revenue month
    columns_to_drop = df_pl.columns[1:df_pl.shape[1]-2]
    df_pl = df_pl.drop(columns=columns_to_drop)

    df_pl.columns = ['Well Name', 'Recent Month P&L', 'YTD P&L']
    df_pl = df_pl.round({'Recent Month P&L': 0, 'YTD P&L': 0})
    df_pl = df_pl.fillna('')

    print(df_pl)
    
    # Update the month each time program runs
    df_pl['Date'] = 'Apr 2023'
    df_pl.to_json("../frontend/data/econ/economics.json", orient='records')
    #df_pl.to_json("../STprodWebsite/STprod/static/economics.json", orient='records')
    #path to (frontend) data/econ/economics.json

    # PAYOUTS
    df = pd.read_excel('payouts.xlsx', usecols='A,T')
    df_payouts = df.copy()
    df_pl.to_json("../frontend/data/econ/payouts.json", orient='records')
    #df_payouts.to_json("../STprodWebsite/STprod/static/payouts.json", orient='records')
    #path to (frontend) data/econ/payouts.json

if __name__ == '__main__':
    main()
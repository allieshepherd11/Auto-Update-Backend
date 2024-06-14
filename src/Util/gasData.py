import json
import pandas as pd
from collections import defaultdict
import numpy as np

def stats():
    with open('data/misc/groupedLineData.json', 'r') as f:
        databook = json.load(f)
    print(databook['Aaron #1'].keys())

    res = []
    for well,data in databook.items():
        if well != 'J Beeler #1':continue
        print(well)
        vals = []
        for readingType,reading in data.items():
            for date,linkedData in reading.items():
                vals = sorted([float(x) for x in linkedData['val']])
                print(date)
                print('MAX',max(vals))
                print('MIN',min(vals))
                print('AVG',sum(vals)/len(vals))
                print('MEDIAN',vals[round(len(vals)/2)])

def private_pd_merge(df:pd.DataFrame):

    print(df.columns)

    return

def format_from_fe():
    with open('../frontend/data/ST/gasData.json', 'r') as f: data = json.load(f)

    df = pd.read_csv('data/prod/ST/data.csv')

    dfGas = defaultdict(list)
    wells = sorted(set([e[0] for e in data]))
    dates = set([e[1] for e in data])


    for well in wells:
        #if well != 'Dillard #1':continue
        print(well)

        fData = [entry for entry in data if entry[0] == well]
        for d in dates:
            ffData = [entry for entry in fData if entry[1] == d]

            check = {'Sales Pressure':0,'Flow Rate Sales':0,'Flow Rate Flare':0}
            dfGas['Well Name'].append(well)
            dfGas['Date'].append(d)
            for entry in ffData:
                check[entry[2]] = 1
            
                dfGas[entry[2]].append(entry[3])

            for ty,entered in check.items():
                if not entered:
                    dfGas[ty].append(np.nan)
    print(dfGas)

    pd.DataFrame(dfGas).to_csv('dfGas.csv',index=False)

if __name__  == '__main__':
    dfprod = pd.read_csv('data/prod/ST/data1.csv')
    dfgas = pd.read_csv('data/prod/ST/gasData.csv')

    l = len(dfgas)
    for idx,row in dfgas.iterrows():
        print(l-idx)
        mask = (dfprod['Well Name'] == row['Well Name']) & (dfprod['Date'] == row['Date'])
        dfprod.loc[mask, ['Sales Pressure', 'Flow Rate Flare', 'Flow Rate Sales']] = row["Sales Pressure"], row["Flow Rate Flare"], row["Flow Rate Sales"]

    dfprod.to_csv('data/prod/ST/datacombo.csv',index=False)
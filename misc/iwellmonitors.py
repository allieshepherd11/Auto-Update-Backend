import pandas as pd
from collections import defaultdict
from datetime import datetime
from src.Modules.iWell import IWell

def etpumpdia():
    importPath="C:/Users/plaisancem/Downloads/x.csv"
    df = pd.read_csv(importPath)
    dfetprod = pd.read_excel("C:/Users/plaisancem/CML Exploration/Travis Wadman - CML/East Texas/East Texas Production Tracker - Copy.xlsx")
    df = df[(~df['Strokes Per Minute (SPM)'].isna())].reset_index(drop=True)
    df['Date'] = pd.to_datetime(df['Date'] + ' ' + df['Time'],format='mixed')

    df = df.loc[df.groupby('Well Name')['Date'].idxmax()]
        
    for _,row in df.iterrows():
        well = row['Well Name']
        mask = dfetprod['Well Name'] == well

        if mask.any():
            pumpDiam = dfetprod.loc[mask,'Pump Diameter'].tolist()[0]
            if pumpDiam != row['Plunger Diameter (in)']:
                print(f'{well} wrong')

        else:
            print(f'{well} not found')

def iwellmeters():
    df = pd.read_csv('data/prod/ST/data.csv')
    since = datetime.strptime(str('2024-11-19'), "%Y-%m-%d").timestamp()
    st = IWell('SOUTH TEXAS','ST',since)

    res = defaultdict(list)
    for well,data in df.groupby('Well Name'):
        #if well != 'Pickens #1':continue
        print(well)
        if well not in st.wells.keys():
            print('Not in st wells',well)
            continue

        res['Well'].append(well)
        monitors = st.GET_wellMeters(st.wells[well])
        res['Meters'].append(len(monitors))
        meternames = [m['name'] for m in monitors]
        res['Meter Names'].append(' - '.join(meternames))
        flareMeter = False
        for mn in meternames: 
            if 'flare' in mn.lower():flareMeter = True

        for field in ['Flow Rate Sales','Sales Pressure','Flow Rate Flare']:
            d = data[field][:1].tolist()[0]
            dDate = data['Date'][:1].tolist()[0]

            if d == d:
                data['diff'] = data[field].diff().ne(0)
                t=data['diff'][:10].tolist()
                if field == 'Flow Rate Sales':
                    dGas = df.loc[(df['Well Name'] == well) & (df['Date'] == dDate),'Gas (MCF)'][:1].to_list()[0]
                    if d == dGas:
                        res[field].append('Up')
                        continue
                if t.count(True) > 1:
                    res[field].append('Up')
                    continue
            if field == 'Flow Rate Flare' and not flareMeter:
                res[field].append('')
                continue
            res[field].append('Down')

    pd.DataFrame(res).to_csv('IwellMonitorspy.csv',index=False)


if __name__ == "__main__":
    since = datetime.strptime(str('2024-11-20'), "%Y-%m-%d").timestamp()
    iw = IWell('Remote Monitors','RM',since)
    tanks = iw.GET_tanks()
    res = defaultdict(list)
    print(iw.wells.keys())
    for rw,rwId in iw.wells.items():
        #if rw != 'Aaron #1 Remote':continue
        print(rw)

        meters = iw.GET_wellMeters(rwId)
        tanks = iw.GET_wellTanks(rwId)
        print(meters)
        print(tanks)
        working = [False,False]
        for idx,tank in enumerate(tanks):
            rd = iw.GET_tankReading(tank['id'])
            if len(rd) > 0:
                res[f'Tank{idx+1}'].append(tank['name'])
                res[f'Tank{idx+1}Status'].append('Up')
        
        res['Well'].append(rw)
        for idx in range(0,2):
            for col in [f'Tank{idx+1}',f'Tank{idx+1}Status']:
                if len(res[col]) != len(res['Well']):
                    res[col].append('')
    pd.DataFrame(res).to_csv('tankstatusIwell.csv',index=False)
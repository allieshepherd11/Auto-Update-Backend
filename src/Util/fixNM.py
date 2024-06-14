from src.Modules.iWell import IWell
from datetime import datetime
from collections import defaultdict
import json

def fixAllocations():
    unix = int( datetime.strptime('2024-03-01', '%Y-%m-%d').timestamp())
    iw = IWell('New Mexico','NM',unix)
    with open('data\\prod\\NM\\allocations.json','r') as f: data = json.load(f)

    mnths = [
        ['2024-01-01','2024-01-31'],
        ['2024-02-01','2024-02-29'],
        ['2024-03-01','2024-03-31'],
        ['2024-04-01','2024-04-30'],
        ['2024-04-01','2024-04-30'],
    ]

    for w,wId in iw.wells.items():
        wId = str(wId)
        if wId in data.keys():
            print(w)
            for s,e in [['2024-05-01','2024-05-31']]:
                print(s)
                tnum = iw.GET_wellFieldValue(wId,'805',[s,e])
                testprod = [iw.GET_wellFieldValue(wId,key,[s,e])  for key in [806,855,807]]#oil,gas,water
                
                twell = defaultdict(str)
                for test in tnum: 
                    dt = datetime.fromtimestamp(test['reading_time'])
                    if datetime.strptime(s, '%Y-%m-%d') <= dt <= datetime.strptime(e, '%Y-%m-%d'):
                        twell[dt.strftime('%Y-%m-%d')] = str(test['value'])
                tprod = defaultdict(dict)
                for i in range(len(testprod)):
                    for rd in testprod[i]:
                        dstr = datetime.fromtimestamp(rd['reading_time']).strftime('%Y-%m-%d')
                        tprod[dstr][['oil','gas','water'][i]] = float(rd['value'])
                
                res = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
                for date,tW in twell.items():
                    prod = tprod[date] 
                    for k,v in prod.items():
                        res[s[:7]][tW][k].append(v)
                data[wId]['tests'].update(res)

    with open('data\\prod\\NM\\allocations.json', 'w') as f:
        json.dump(data, f, indent=4)


def fillinIds():
    with open('data\\prod\\NM\\allocations.json','r') as f: data = json.load(f)
    for _,book in data.items():
        wids = book['wells']
        for mnth,tests in book['tests'].items():
            for wid in wids: 
                if wid not in tests.keys():
                    print(mnth)
                    print(wid)
                    print(book['name'])
                    book['tests'][mnth][wid] = {'oil':[],'water':[],'gas':[]}
                    print(book['tests'][mnth])

    with open('data\\prod\\NM\\allocations.json','w') as f: json.dump(data,f)
       
    return
if __name__ == '__main__':
    fillinIds()



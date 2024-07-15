import requests,os
import json,pandas as pd

def inactiveW():
    #with open('allWells.json', 'r') as f:
    #    data = json.load(f)
    #dfs=pd.DataFrame()
    #for root,folders,files in os.walk('data/prod'):
    #    for file in files:
    #        if file == 'data.csv':
    #            dfs=pd.concat([dfs,pd.read_csv(root+'/'+file)])
    #wells = sorted(set(dfs['Well Name'].tolist()))
    #print(wells)
    #with open('savedWells.json', 'w') as f:
    #    json.dump(wells,f)
    with open('data/misc/allWells.json', 'r') as f:
        inactiveWells = json.load(f)
    with open('data/misc/savedWells.json', 'r') as f:
        data = json.load(f)
    with open('data/misc/wnMap.json', 'r') as f:
        renames = json.load(f) 
    inactiveWells = {w.lower():w for w in inactiveWells.keys()}
    data = [w.lower() for w in data]
    keys = ['remote', 'test','battery','sales','swd','inj','compressor','drip']
    drop = set()
    missing = set()
    for well in inactiveWells.keys():
        if well not in data:
            missing.add(well)
            for key in keys:
                if key in well.lower():
                    drop.add(well)  
    missing = sorted([inactiveWells[w] for w in list(missing) if w not in list(drop)])
    print(missing)
    missing = [w for w in missing if w.title() not in renames.keys()]
    with open('missingWells.json', 'w') as f:
        json.dump(missing,f)
    return

if __name__ == '__main__':
    with open('data/misc/allWells.json', 'r') as f:
        allWells = json.load(f)
    with open('data/misc/missingWells.json', 'r') as f:
        data = json.load(f)
    print(allWells)
    data = {w:allWells[w] for w in data}
    print(data)
    with open('data/misc/missingWells.json', 'w') as f:
        json.dump(data,f)
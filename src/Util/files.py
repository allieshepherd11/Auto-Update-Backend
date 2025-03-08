import os
import json
from collections import defaultdict
from itertools import zip_longest
import pandas as pd
import time
from datetime import datetime

def openFiles():
    import webbrowser
    import os

    path = "G:/CML Operations/WELL FILES"
    df = pd.read_excel("book5.xlsx")
    wells = df['Well'].tolist()
    do = []
    files = sorted([f for f in os.listdir(path)])
    for f in files:
        if f not in wells:continue
        rprtsDir = f'{path}/{f}/REPORTS-DAILY OPS/Individual Reports/'
        if os.path.exists(rprtsDir):
            do.append(f)

    do = sorted(do)
    for f in do:
        print(f)
        rprtsDir = f'{path}/{f}/REPORTS-DAILY OPS/Individual Reports/'
        files = [f for f in os.listdir(rprtsDir) if os.path.isfile(os.path.join(rprtsDir, f))]
        files.sort(key=lambda x: os.path.getmtime(os.path.join(rprtsDir, x)), reverse=True)
        if len(files) > 0:
            webbrowser.open_new_tab(rprtsDir+'/'+files[0])
            time.sleep(1)

def walkPath(keys,path="C:/"):
    #path = "C:/Users/plaisancem/CML Exploration/Brandon Rogers - Well Files/"
    res = defaultdict(list)
    for root,folders,files in os.walk(path):
        for fld,f in zip_longest(folders,files):
            for key in keys:
                k = key.lower()
                if fld:
                    if k in fld.lower():
                        print(root,fld)
                        res[root].append(fld)
                if f:
                    if k in f.lower():
                        file_path = os.path.join(root, f)
                        modified_time = os.path.getmtime(file_path)
                        modified_date = datetime.fromtimestamp(modified_time)
                        print(root,f)
                        res['root'].append(root)
                        res['file'].append(f)
                        res['time'].append(modified_date)


    print(res)
    df = pd.DataFrame(res)
    df.to_csv('keys.csv')

if __name__ == '__main__':
    walkPath(keys=['.xlsx'],path="C:/")
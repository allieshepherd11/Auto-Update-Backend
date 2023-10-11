import pandas as pd
import json 

dfpl = pd.read_json('data\econ\plData.json').fillna(0)
with open('data\econ\well_map.json', 'r') as f:
    dmap = json.load(f)

for key,val in dmap.items():
    mask = dfpl["Well Number"] == key
    idx = dfpl.index[mask].tolist()[0]
    dfpl.loc[idx,'Well Name'] = val
print(dfpl)

d = dfpl.to_dict(orient='index')
res = {}
for key,inner in d.items(): 
    for k,v in inner.items():
         if isinstance(v,str):
            if "-" in v:
                inner[k] = 0
    res[inner["Well Name"]] = inner
print(res)
exit()
with open('db/econ/pl16_23res.json', 'w') as json_file:
        json.dump(res, json_file)
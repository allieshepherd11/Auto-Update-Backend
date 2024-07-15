import pandas as pd,json
from collections import defaultdict

dfline = pd.read_csv("./ST line coordinates.csv")
dfwells = pd.read_csv("C:\\Users\\plaisancem\\Downloads\\ST well coordinates.csv")
#seen = set()
#cnt = 1
#dfline['num'] = 0
#for idx,row in dfline.copy().iterrows():
#    if row['name'] in seen:
#        cnt += 1
#        dfline.iloc[int(idx), dfline.columns.get_loc('num')] = cnt
#    else:
#        seen.add(row['name'])
#        cnt = 0
#        
#print(dfline)
#dfline.to_csv('ST line coordinates.csv',index=0)
#exit()

matches = defaultdict(dict)

for _,rowWell in dfwells.iterrows():
    for _,rowLine in dfline.iterrows():
        diffLat = abs(rowWell['lat'] - rowLine['lat'])
        diffLng = abs(rowWell['lng'] - rowLine['lng'])
        diff = diffLat + diffLng
        try:
            lastClosest = matches[rowWell['name']]['diff']
        except KeyError:
            lastClosest = 1e10
        if diff < lastClosest:
            matches[rowWell['name']]['pipline'] = rowLine['name']
            matches[rowWell['name']]['num'] = rowLine['num']
            matches[rowWell['name']]['diff'] = diff

with open('matches.json', 'w') as f:
    json.dump(matches,f)


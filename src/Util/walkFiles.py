import os
import json
from collections import defaultdict
from itertools import zip_longest



path = "G:\\"
#path = "C:/Users/plaisancem/CML Exploration/Brandon Rogers - Well Files/"
keys = [' esa ','energy service agreement']
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
                    print(root,f)
                    res[root].append(f)
print(res)
with open('tripleSale.json', 'w') as f:
    json.dump(res,f)
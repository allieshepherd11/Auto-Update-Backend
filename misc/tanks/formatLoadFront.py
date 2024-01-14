import pandas as pd
import json
from datetime import datetime
with open("data\prod\ST\loads.json","r") as f: data=json.load(f)

print(data)
loads_display = []
for well,tanks in data.items():
    for _,tank in tanks.items():
        for load in tank:
            print(tank)
            loads_display.append([
                well,
                load['tank_id'],
                load['type'],
                load['bbls'],
                datetime.fromtimestamp(load['dt']).strftime('%m-%d-%y %H:%M:%S'),
            ])
print(loads_display)
with open('../frontend\data\ST/loads1.json','w') as f: json.dump(loads_display,f)


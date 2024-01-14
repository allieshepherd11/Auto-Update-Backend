import iWell
from datetime import datetime,timedelta
import time
import requests
from dotenv import load_dotenv
import time
import json
import pandas as pd


class WellBattery:
    def __init__(self,wellName,wellId,token,since) -> None:
        self.wellName = wellName
        self.wellId = wellId
        self.token = token
        self.since = since
        self.folder_path = "data/prod/ST/tanks/"

    def handle(self):
        tank_levels,runtickets = self.get_tank_levels()

        return tank_levels,runtickets

    def req_wrapper(self,url):
        try: 
            x = requests.get(url,headers={'Authorization': f'Bearer {self.token}'})
        except requests.exceptions.ConnectionError:
            print('connection error')
            time.sleep(10);print('trying again..\n')
            return self.req_wrapper(url) 
        return x.json()['data']
    
    def get_tank_levels(self):
        battery = self.req_wrapper(f"https://api.iwell.info/v1/wells/{self.wellId}/tanks")
        tank_levels = []
        run_tickets = pd.DataFrame()

        for tank in battery:
            readings = self.req_wrapper(f"https://api.iwell.info/v1/tanks/{tank['id']}/readings?since={self.since}")
            info = self.req_wrapper(f"https://api.iwell.info/v1/tanks/{tank['id']}")
           
            readings.sort(key=lambda x: x["reading_time"])
            if len(readings) != 0:
                tank_levels.append({
                    "Id":readings[-1]["id"],
                    "type": tank['type'],
                    "name": tank['name'],
                    "capcity": info['capacity'],
                    "factor": info['multiplier'],
                    "reading_time":readings[-1]["reading_time"],
                    "top_feet":readings[-1]["top_feet"],
                    "top_inches":readings[-1]["top_inches"],
                    "updated_at":readings[-1]["updated_at"],
                })

        return tank_levels,run_tickets
    
    def get_reading_runtickets(self,tank,readings):
        for reading in reversed(readings):
            run_ticket = self.runtickets(self.well,tank['id'],reading['id'])
            run_tickets = pd.concat([run_ticket,run_tickets])
    
def flatten_recursive(arr):
    result = []
    for item in arr:
        if isinstance(item, list):
            result.extend(flatten_recursive(item))
        else:
            result.append(item)
    return result

def callable_loads():
    equalized=figure_equalized_tanks()
    with open("data/prod/ST/batteries.json","r") as f: data=json.load(f)

    load = {'OIL': 200,'WATER':140,'OIL/WATER':140}
    res = {}
    for well,tanks in data.items():
        equal_tanks_groups = equalized[well]
        equal_tanks = flatten_recursive(equal_tanks_groups)

        loads = {}
        seen = []
        
        for tank in tanks:
            tankId = tank['Id']
            if tankId in seen: continue

            loads[tankId] = []
            if tankId not in equal_tanks:
                amt = load[tank['type']]
                bbls = (tank['top_feet']*12 + tank['top_inches'])*tank['factor']
                
                for _ in range(int(bbls // amt)):
                    loads[tankId].append({
                        'tank_id':tankId,
                        'dt':tank['updated_at'],
                        'type':tank['type'],
                        'bbls':amt,
                    })
            else:
                our_group = []
                for group in equal_tanks_groups:
                    for tankID in group: 
                        if tankId == tankID: our_group = group

                bbls = (tank['top_feet']*12 + tank['top_inches'])*tank['factor']*(len(our_group))
                for _ in range(int(bbls // 200)):
                    loads[tankId].append({
                        'tank_id':our_group,
                        'dt':tank['updated_at'],
                        'type':tank['type'],
                        'bbls':200,
                    })

                for tankID in our_group: seen.append(tankID)
                
                

        res[well] = loads
    with open("data/prod/ST/tanks/loads.json",'w') as f: json.dump(res,f)
    fs_loadsFE(res)
    return 

def save_runtickets(imports):
        df = pd.concat([pd.read_csv('data/prod/ST/runtickets.csv'),imports])
        df['updated_at'] = pd.to_datetime(df['updated_at'])

        df = df.sort_values(by=['id', 'updated_at'], ascending=[True, False])
        df = df.drop_duplicates(subset='id', keep='first').reset_index(drop=True)
        df = df.sort_values(['well', 'date'], ascending = [True , False]).reset_index(drop=True)
        print("DF",df)
        df.to_csv('runticketsCurr.csv',index=False)
        return

def fs_loadsFE(data):
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
    with open('../frontend\data\ST/loads.json','w') as f: json.dump(loads_display,f)

def fs_batteriesFE():
    with open(f"data/prod/ST/batteries.json",'r') as f: batteries=json.load(f)
    all_tanks = [{
            'bbl':0,
            'type':'OIL',
            'capcity':0,
            'factor':1.67,
            'name':'All Tanks Oil',
            'Id':0
        },{
            'bbl':0,
            'type':'WATER',
            'capcity':0,
            'factor':1.67,
            'name':'All Tanks Water',
            'Id':0
        }
    ]

    for _,tanks in batteries.items():
        for tank in tanks:
            bbl = (tank['top_feet']*12 + tank['top_inches'])*tank['factor']
            if tank['type'] == 'OIL': 
                all_tanks[0]['bbl'] += bbl
                all_tanks[0]['Id'] += 1
                all_tanks[0]['capcity'] += tank['capcity']
            else: 
                all_tanks[1]['bbl'] += bbl
                all_tanks[1]['Id'] += 1
                all_tanks[1]['capcity'] += tank['capcity']
    all_tanks[0]['name'] = f'All Tanks Oil ({all_tanks[0]["Id"]})'
    all_tanks[1]['name'] = f'All Tanks Water ({all_tanks[1]["Id"]})'
    batteries['All'] = all_tanks
    with open(f"../frontend/data/ST/batteries.json",'w') as f: json.dump(batteries,f)

    return batteries

def figure_equalized_tanks():
        with open(f"data\prod\ST/batteries.json","r") as f: data=json.load(f)
        equalized = {}
        for well,tanks in data.items():
            print(well)
            equalized[well] = []
            oil={}
            for tank in tanks:
                if tank['type'] == 'WATER': continue

                bo = (tank['top_feet']*12 + tank['top_inches'])*tank['factor']
                if bo not in oil: oil[bo] = [tank['Id']]
                else: oil[bo].append(tank['Id'])
            for amt,ids in oil.items():
                if len(ids) > 1:
                    equalized[well].append([i for i in ids])

        with open(f"data\prod\ST/equalized.json","w") as f: json.dump(equalized,f)
        return equalized

if __name__ == '__main__':
    callable_loads()
    fs_batteriesFE()
    exit()
    token = iWell.init()
    well = 'Little 179 #1'
    wellId = iWell.get_wellId(token,'SOUTH TEXAS',well)
    since = int(datetime.strptime('2024-01-07','%Y-%M-%d').timestamp())

    little = WellBattery(well,wellId,token,since)
    tank_levels, _ = little.get_tank_levels()
    print(tank_levels)
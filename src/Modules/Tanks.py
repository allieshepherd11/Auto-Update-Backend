import src.Modules.iWell as iWell
from datetime import datetime,timedelta
import time
import requests
from dotenv import load_dotenv
import time
import json
import pandas as pd
from collections import defaultdict
import math
import re
import src.Modules.Field as tankFld



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

def days_to_fill(well,battery,df):
    if well == 'Joseph #1': return -1
    avgOil = df.loc[df[0].str.lower() == well.lower()].reset_index(drop=True).iloc[0:30,10].mean()
    avgWater = df.loc[df[0].str.lower() == well.lower()].reset_index(drop=True).iloc[0:30,11].mean() - avgOil
    tot=defaultdict(int)

    for tank in battery:
        avgF = avgOil if tank['type'] == 'OIL' else avgWater
        if avgF != 0:
            tot[tank['type']] += round((tank['capcity'] - (tank['top_feet']*12 + tank['top_inches'])*tank['factor']) / avgF,2)
        else:
            tot[tank['type']] = -1
    
    return tot

def callable_loads():
    equalized=figure_equalized_tanks()
    with open("data/prod/ST/tanks/batteries.json","r") as f: data=json.load(f)
    #dfProd = pd.read_csv('data/prod/')
    load = {'OIL': 200,'WATER':140,'OIL/WATER':140}
    res = {}
    for well,tanks in data.items():
        #if well != 'Beeler #17':continue
        print(well)
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
                        'tank_name':tank['name'],
                        'dt':tank['updated_at'],
                        'type':tank['type'],
                        'bbls':amt,
                    })
            else:
                our_group = []
                for group in equal_tanks_groups:
                    for tankId_name in group: 
                        if tankId == tankId_name[0]: our_group = group

                bbls = (tank['top_feet']*12 + tank['top_inches'])*tank['factor']*(len(our_group))

                for _ in range(int(bbls // 200)):
                    loads[tankId].append({
                        'tank_id':[i[0] for i in our_group],
                        'tank_name':[i[1] for i in our_group],
                        'dt':tank['updated_at'],
                        'type':tank['type'],
                        'bbls':200,
                    })

                for tankId_name in our_group: 
                    seen.append(tankId_name[0])
        
        res[well] = loads
    with open("data/prod/ST/tanks/loads.json",'w') as f: json.dump(res,f)
    
    return res

def fs_loadsFE(data):
    dfprod = pd.read_json('data/prod/ST/data.json')
    with open("data/prod/ST/tanks/batteries.json","r") as f: battery=json.load(f)

    loads_display = []
    for well,tanks in data.items():
        print(well)
        dtf = days_to_fill(well,battery[well],dfprod)
        for _,tank in tanks.items():
            for load in tank:
                loads_display.append([
                    well,
                    load['tank_id'],
                    load['type'],
                    load['bbls'],
                    datetime.fromtimestamp(load['dt']).strftime('%m-%d-%y %H:%M:%S'),
                    round(dtf[load['type']],2),
                    load['tank_name']
                ])
    with open('../frontend/data/ST/loads.json','w') as f: json.dump(loads_display,f)
    with open('data/prod/ST/tanks/loadsDisplay.json','w') as f: json.dump(loads_display,f)

    return loads_display
   
def fs_batteriesFE():
    with open(f"data/prod/ST/tanks/batteries.json",'r') as f: batteries=json.load(f)
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
        with open(f"data/prod/ST/tanks/batteries.json","r") as f: data=json.load(f)
        equalized = defaultdict(list)
        for well,tanks in data.items():
            oil=defaultdict(list)
            for tank in tanks:
                if tank['type'] == 'WATER': continue

                bo = (tank['top_feet']*12 + tank['top_inches'])*tank['factor']
                oil[bo].append([tank['Id'],tank['name']])
                #if bo not in oil: oil[bo] = [[tank['Id'],tank['name']]]
                #else: oil[bo].append([tank['Id'],tank['name']])
            for amt,idName in oil.items():
                if len(idName) > 1:
                    equalized[well].append(idName)
        with open(f"data/prod/ST/tanks/equalized.json","w") as f: json.dump(equalized,f)
        return equalized

def save_runtickets(imports):
    df = pd.concat([pd.read_csv('data/prod/ST/runtickets.csv'),imports])
    df['updated_at'] = pd.to_datetime(df['updated_at'])

    df = df.sort_values(by=['id', 'updated_at'], ascending=[True, False])
    df = df.drop_duplicates(subset='id', keep='first').reset_index(drop=True)
    df = df.sort_values(['well', 'date'], ascending = [True , False]).reset_index(drop=True)
    print("DF",df)
    df.to_csv('runticketsCurr.csv',index=False)
    return

def sendLoads(data=None):
    if not data: 
        with open('data/prod/ST/tanks/loads.json','r') as f: data = json.load(f)
    with open("data/prod/ST/tanks/batteries.json","r") as f: battery=json.load(f)
    dfprod = pd.read_json('data/prod/ST/data.json')

    sheet = defaultdict(list)
    for well,tanks in data.items():
        print(well)
        #if well != 'Dixondale #1':continue
        dtf = days_to_fill(well,battery[well],dfprod)
        w = re.sub(r'[^a-zA-Z]', '', well)
        for _,loads in tanks.items():
            if loads == []:continue
            load = loads[0]
            sheet['Well Name'].append(well)
            sheet['Loads'].append(len(loads))
            sheet['Type'].append(load['type'])
            sheet['Dayts to Fill'].append(dtf[load['type']])

            if isinstance(load['tank_name'],list):
                sheet['Tank'].append(', '.join(load['tank_name']))
                sheet['Equalized'].append(len(load['tank_name']))
            else:
                sheet['Equalized'].append('')
                sheet['Tank'].append(load['tank_name'])

            sheet['As of'].append(datetime.fromtimestamp(load['dt']).strftime('%Y-%m-%d %H:%M:%S'))


    pd.DataFrame(sheet).to_csv(f'data/prod/ST/tanks/oilLoads {datetime.now().strftime("%Y-%m-%d")}.csv',index=False)
    return

def run():
    start = (datetime.now() - timedelta(1)).strftime('%Y-%m-%d')
    print(start)
    ##
    fld = tankFld.Field('SOUTH TEXAS','ST',start)
    fld.importTankData()
    loads = callable_loads()
    fs_loadsFE(loads)
    fs_batteriesFE()
    sendLoads(loads)

if __name__ == '__main__':
    run()
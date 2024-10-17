try:
    import src.Modules.iWell as iWell
except ModuleNotFoundError:
    import iWell 
from functools import reduce
from datetime import datetime,timedelta
import time
import requests
import os 
from dotenv import load_dotenv
import time
import json
import pandas as pd
#from Tanks import WellBattery,format_save_loads,callable_loads,save_runtickets
from collections import defaultdict
import numpy as np
import calendar


class Field():
    def __init__(self,field,abbr,start,range=None) -> None:
        self.field = field
        self.abbr = abbr
        self.start = start
        self.since = start
        if start:
            self.since = datetime.strptime(str(start), "%Y-%m-%d").timestamp()
            self.imprtDays = self.dStrs(start,str(datetime.today().date()))

        self.IWell = iWell.IWell(field,abbr,self.since,range)
        with open('data/prod/ST/lastpullRT.json','r') as f: self.since_tanks = json.load(f)
        
    def __repr__(self):
        return '/n'.join([
            f'Field: {self.field}',
            f'User: {self.me()}',
            f'Num Wells: {len(self.wells)}'])
    
    def importData(self):
        #since = datetime.strptime(str(self.start), "%Y-%m-%d").timestamp()
        updates = []
        importData = []
        batteries = {}
        dfGasImport = pd.DataFrame()
        runtickets = pd.DataFrame()
        for well,id in self.IWell.wells.items():
            if 'Compressor' in well or 'Drip' in well or 'SWD' in well: continue
            #if well != 'Pfeiffer #1':continue
            print(well)
            if self.abbr == 'ST': 
                dfGasImport = pd.concat([dfGasImport,self.importGasData(id,well)]).drop_duplicates()
                batteries[well],well_tickets = self.tank_levels(well,id)
                runtickets=pd.concat([runtickets,well_tickets])
                
            prod = self.IWell.GET_wellProduction(id)
            comms = self.IWell.GET_wellComments(id)
            tp = self.IWell.GET_wellFieldValue(id,607)
            cp = self.IWell.GET_wellFieldValue(id,1415)
        
            for i in prod[:]:
                if i["production_time"] != i["updated_at"] and i["production_time"] < self.since:#gets updated prod, but not updates since last import
                    i["Well Name"] = well
                    updates.append(i)
                    prod.remove(i)

            for i in prod[:]:# copy of list
                if i["date"] == str(datetime.today().date()) or i["date"] == str(self.start) or time.mktime(datetime.strptime(i["date"], "%Y-%m-%d").timetuple()) < self.since: prod.remove(i)
            
            if prod == []:#needs fix
                continue
            
            #check if shared battery
            alct_path = f'data/prod/{self.abbr}/allocations.json'
            if os.path.exists(alct_path):
                alct = pd.read_json(alct_path).to_dict()
                if (id in alct.keys()): 
                    sharedBatt = Allocations(self.IWell,id,prod,comms,alct_path,self.imprtDays).allocate()
                    for entry in sharedBatt: 
                        importData.append(entry)
                    continue
                
            cpAvg,tpAvg = 0,0

            if len(cp) > 0:
                if 'value' in cp[-1].keys():
                    cpAvg = cp[-1]['value']
            if len(tp) > 0:
                if 'value' in tp[-1].keys():
                    tpAvg = tp[-1]['value']

            for i in range(len(prod)):
                date = prod[i]["date"]
                data = [well,prod[i]["date"],prod[i]["oil"],prod[i]["gas"],prod[i]["water"],tpAvg,cpAvg]
                for c in range(len(comms)):
                    dt = datetime.fromtimestamp(comms[c]['note_time']).strftime('%Y-%m-%d')
                    if dt == date: 
                        data.append(comms[c]['message'])
                        break
                
                if len(data) == 7: data.append("")
                importData.append(data)
                
        
        if self.abbr == 'ST': 
            with open(f"data/prod/ST/tanks/batteries.json",'w') as f: json.dump(batteries,f)
            runtickets.to_json('data/prod/ST/tanks/runtickets.json')
        

        dfimport = pd.DataFrame(data=importData,columns=["Well Name","Date","Oil (BBLS)","Gas (MCF)","Water (BBLS)","TP","CP","Comments"])
        dfimport = dfimport.fillna('')
        dfimport = dfimport.sort_values(['Date', 'Well Name'], ascending = [False , True])
        dfimport.Date = pd.to_datetime(dfimport.Date)
        dfimport = dfimport.reset_index(drop=True)
        return dfimport,updates,batteries,dfGasImport
    
    def importGasData(self,wellId,well):
        res = defaultdict(dict)
        def da(data,ty):
            groupedData = defaultdict(list)
            #dates = ['2024-07-20','2024-07-21','2024-07-22']
            for reading in data:
                dt_string = datetime.fromtimestamp(reading['reading_time']).strftime('%Y-%m-%d %H:%M:%S')
                date = dt_string.split(' ')[0]
                groupedData[date].append(reading['value'])

            for date,vals in groupedData.items():
                avg = round(sum([float(x) for x in vals])/len(vals),2)
                res[date][ty] = avg
            return
        
        
        da(self.IWell.GET_wellFieldValue(wellId,4088),'Sales Pressure')
        da(self.IWell.GET_wellFieldValue(wellId,4091),'Flow Rate Sales')
        da(self.IWell.GET_wellFieldValue(wellId,4096),'Flow Rate Flare')

        df=defaultdict(list)
        tys = ['Sales Pressure','Flow Rate Sales','Flow Rate Flare']
        for date,vals in res.items():
            df['Well Name'].append(well)
            df['Date'].append(date)
            for ty in tys:
                if ty in vals.keys():
                    df[ty].append(vals[ty])
                else:
                    df[ty].append(np.nan)
                    

        df=pd.DataFrame(df)
        if 'Date' in df.columns:
            df=df[df['Date'] != self.start]
            df['Date'] = pd.to_datetime(df['Date'])

        return df

    def importTankData(self):
        batteries = {}
        runtickets = pd.DataFrame()
        for well,id in self.IWell.wells.items():
            if 'Compressor' in well or 'Drip' in well or 'SWD' in well: continue
            print(well)
            batteries[well],well_tickets = self.tank_levels(well,id)
            #runtickets=pd.concat([runtickets,well_tickets])

        with open(f"data/prod/ST/tanks/batteries.json",'w') as f: json.dump(batteries,f)
        #runtickets.to_json('data/prod/ST/tanks/runtickets.json')
        return

    def tank_levels(self,well,well_id):
        #since_tanks = self.since_tanks[well.upper()]
        battery = self.IWell.GET(f"https://api.iwell.info/v1/wells/{well_id}/tanks")
        res = []
        run_tickets = pd.DataFrame()
        if battery:
            for tank in battery:
                readings = self.IWell.GET(f"https://api.iwell.info/v1/tanks/{tank['id']}/readings?since={self.since}")
                info = self.IWell.GET(f"https://api.iwell.info/v1/tanks/{tank['id']}")
                #for reading in reversed(readings):
                #    run_ticket = self.runtickets(well,tank['id'],reading['id'])
                #    run_tickets = pd.concat([run_ticket,run_tickets])

                readings.sort(key=lambda x: x["reading_time"])
                if len(readings) != 0:
                    res.append({
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
                    #run_tickets = self.runtickets(well,tank['id'],readings[-1]['id'])

        return res,run_tickets

    def runtickets(self,well,tank_id,reading_id): 
        data = self.req_wrapper(f'https://api.iwell.info/v1/tanks/{tank_id}/readings/{reading_id}/run-tickets?since={self.since}')
        df = {'well':[],'id':[],'run_ticket_number':[],'date':[],'date_string':[],'updated_at':[],'type':[],'total':[]}
        if len(data) > 0:
            for ticket in data:
                df['well'].append(well)
                df['date_string'].append(datetime.utcfromtimestamp(ticket['date']).strftime("%Y-%m-%d %H:%M:%S"))
                
                for key in ticket:
                    if key in ['id','run_ticket_number','date','type','total','updated_at']:
                        df[key].append(ticket[key])
                    #r['tank'] = tank_id
                    #r['reading_id'] = reading_id
                        
        return pd.DataFrame(df)

    def equalized(self):
        with open("data/prod/ST/batteries.json","r") as f: data=json.load(f)
        equalized = {}
        for well,tanks in data.items():
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
        with open("equalized.json","w") as f: json.dump(equalized,f)
        
        return

    def callable_load(self):
        with open("data/prod/ST/equalized.json","r") as f: equalized=json.load(f)
        with open("data/prod/ST/batteries.json","r") as f: data=json.load(f)
        load = {'OIL': 190,'WATER':120,'OIL/WATER':120}
        
        res = {}
        for well,tanks in data.items():
            equal_tanks = equalized[well]

            loads = {}
            for tank in tanks:
                loads[tank['Id']] = []
                amt = load[tank['type']]
                bbls = (tank['top_feet']*12 + tank['top_inches'])*tank['factor']
                
                for _ in range(int(bbls // amt)):
                    loads[tank['Id']].append({
                        'tank_id':tank['Id'],
                        'dt':tank['updated_at'],
                        'type':tank['type'],
                        'bbls':amt,
                    })
            res[well] = loads
        with open('data/prod/ST/loads.json','w') as f: json.dump(res,f)
        return

    def save_runtickets(self,imports):
        df = pd.concat([pd.read_csv('data/prod/ST/runtickets.csv'),imports])
        df['updated_at'] = pd.to_datetime(df['updated_at'])

        df = df.sort_values(by=['id', 'updated_at'], ascending=[True, False])
        df = df.drop_duplicates(subset='id', keep='first').reset_index(drop=True)
        df = df.sort_values(['well', 'date'], ascending = [True , False]).reset_index(drop=True)
        df.to_csv('runticketsCurr.csv',index=False)
        return

    def dStrs(self,start_date, end_date):
        date_format = '%Y-%m-%d'
        date_strings = []
        
        start_date_obj = datetime.strptime(start_date, date_format)
        end_date_obj = datetime.strptime(end_date, date_format)
        
        current_date = start_date_obj + timedelta(days=1)
        while current_date < end_date_obj:
            date_strings.append(current_date.strftime(date_format))
            current_date += timedelta(days=1)
    
        return date_strings
    
    def format_save_loads(self):
        with open("data/prod/ST/loads.json","r") as f: data=json.load(f)
        loads_display = []
        for well,tanks in data.items():
            for _,tank in tanks.items():
                for load in tank:
                    loads_display.append([
                        well,
                        load['tank_id'],
                        load['type'],
                        load['bbls'],
                        datetime.fromtimestamp(load['dt']).strftime('%m-%d-%y %H:%M:%S'),
                    ])
        with open('../frontend/data/ST/loads.json','w') as f: json.dump(loads_display,f)

class Allocations():
    def __init__(self,IWell:iWell.IWell,well_id,prod,comms,alct_path,imprtDays) -> None:
        self.well_id = well_id
        self.prod = prod
        self.comms = comms
        self.alct_path = alct_path
        self.alct_db = pd.read_json(alct_path).to_dict()
        self.well_name = self.alct_db[well_id]['name']
        tnum = IWell.GET_wellFieldValue(well_id,'805')
        testprod = [IWell.GET_wellFieldValue(well_id,key)  for key in [806,855,807]]#oil,gas,water

        twell = {k:None for k in imprtDays}
        
        for test in tnum: twell[datetime.fromtimestamp(test['reading_time']).strftime('%Y-%m-%d')] = str(test['value'])
        tprod = {k:{} for k in imprtDays}
        for comm in comms:
            dstr = datetime.fromtimestamp(comm['note_time']).strftime('%Y-%m-%d')
            if dstr in tprod.keys(): tprod[dstr]['comm'] = comm['message']

        for i in range(len(testprod)):
            for rd in testprod[i]:
                dstr = datetime.fromtimestamp(rd['reading_time']).strftime('%Y-%m-%d')
                if dstr in imprtDays: tprod[dstr][['oil','gas','water'][i]] = float(rd['value'])
        
        for day,prd in tprod.items():
            misses = [i for i in ['oil','gas','water'] if i not in prd.keys()]
            for miss in misses: tprod[day][miss] = 0#tests[id][float(twell[day])][miss]

        self.twell = twell
        if (well_id == 11464): self.twell['2023-08-17'] = '4'
        self.tprod = tprod

    def lstMnthAvg(self,date,wn1,wn2) -> dict:
        lst_mnth = int(datetime.strptime(date,'%Y-%m-%d').timestamp()) - 60*60*24*int(date[-2:])
        lst_mnth = datetime.utcfromtimestamp(lst_mnth).strftime('%Y-%m-%d')[:7]
        tests = self.alct_db[self.well_id]['tests'][lst_mnth]

        print(date)
        #avgs = {f'{w}_{ty}':round(sum(tests[str(w)][ty])/len(tests[str(w)][ty]),2) 
        #        for w in [wn1,wn2,self.twell[date]] for ty in ['oil','gas','water']}
        avgs = {}
        for ty in ['oil','gas','water']:
            for w in [wn1,wn2,self.twell[date]]:
                try:
                    avgs[f'{w}_{ty}'] = round(sum(tests[str(w)][ty])/len(tests[str(w)][ty]),2)
                except ZeroDivisionError:
                    avgs[f'{w}_{ty}'] = 0

        #res = {w:{'oil':[],'gas':[],'water':[]} for w in [wn1,wn2,self.twell[date]]}
        #for k,v in avgs.items():
        #    unpack = k.split('_')
        #    res[int(unpack[0])][unpack[1]].append(v)
        #print(f'res {res}')
        #self.alct_db[self.well_id]['tests'][date[:7]] = res
        #with open('data/prod/NM/allocations.json','w') as f:
        #    json.dump(self.alct_db,f)
        return  avgs

    def assignComm(self,comm,commtw,*wells):
        splt_comm = {w:'' for w in wells}
        for k in splt_comm.keys(): 
            if str(k) in comm: splt_comm[k] = comm
        s = set(splt_comm.values()); s.add(commtw)   
        if len(s) == 1 and '' in s: splt_comm = {w:comm for w in wells}    

        return splt_comm

    def workoutAvgs():
        return
    
    def allocate(self) -> list:
        typs = ['oil','gas','water']
        res = []
        for day in self.prod:
            date = day['date']
            comm = self.tprod[date]['comm'] if 'comm' in self.tprod[date].keys() else ""
            shtIn = self.alct_db[self.well_id]['shutIn'][date] if date in self.alct_db[self.well_id]['shutIn'].keys() else []
            
            wells_cpy = self.alct_db[self.well_id]['wells'][:]
            if self.twell[date] in wells_cpy: wells_cpy.remove(self.twell[date])

            if self.twell[date] is None or self.twell[date] not in self.alct_db[self.well_id]['wells']:#no test well
                if len(shtIn) == 1 and len(wells_cpy) == 2:
                    wn1 = wells_cpy.pop(); wn2 = wells_cpy.pop()
                    if comm != "": comm = self.assignComm(comm,wn1,wn2)
                    wellNum = wn2 if str(wn1) in shtIn else wn1
                    res.append([f'{self.well_name} #{wellNum}',date,day['oil'],day['gas'],day['water'],"0","0",comm[wellNum]])
                    res.append([f'{self.well_name} #{shtIn[0]}',date,0,0,0,"0","0",f"shut in, {comm[shtIn[0]]}"]);continue                    
                else: self.twell[date] = wells_cpy[0];comm = f'{comm} no test well set, {wells_cpy[0]} used as test'#3 wells ; need to check shtin
            
            lft = [float(day[ty]) - self.tprod[date][ty] for ty in typs];lft = [max(0, val) for val in lft]
            o_lft,g_lft,w_lft = lft[0],lft[1],lft[2]
            
            commtw = comm if str(self.twell[date]) in comm else ''
            res.append([f'{self.well_name} #{self.twell[date]}',date,self.tprod[date]['oil'],
                        self.tprod[date]['gas'],self.tprod[date]['water'],"0","0",commtw])

            if len(self.alct_db[self.well_id]['wells']) == 2:
                wellNum = wells_cpy.pop(); comm1 = comm if str(wellNum) in comm else ''
                if commtw == '' and comm != '': comm1 = comm
                res.append([f'{self.well_name} #{wellNum}',date, o_lft, g_lft, w_lft,"0","0",comm1])

            if len(self.alct_db[self.well_id]['wells']) == 3:
                wn1 = wells_cpy.pop(); wn2 = wells_cpy.pop(); comm = self.assignComm(comm,commtw,wn1,wn2)
                prevAvgs = self.lstMnthAvg(date,wn1,wn2)

                try: tests = self.alct_db[self.well_id]['tests'][date[:7]]
                except KeyError: #first of mnth
                    avgs = prevAvgs
                    self.alct_db[self.well_id]['tests'][date[:7]] = {w:{'oil':[],'gas':[],'water':[]}
                                                                      for w in [wn1,wn2,self.twell[date]]}
                    tests = self.alct_db[self.well_id]['tests'][date[:7]]

                if self.twell[date] in shtIn: exit(print(f'Error: test well {self.twell[date]} is shut in'))
                
                if len(shtIn) == 1:
                    wellNum = wn2 if int(wn1) in shtIn else wn1
                    res.append([f'{self.well_name} #{wellNum}',date, o_lft,g_lft, w_lft,"0","0",comm[wellNum]])
                    res.append([f'{self.well_name} #{shtIn[0]}',date,0,0,0,"0","0",f"shut in, {comm[shtIn[0]]}"])
                    
                if len(shtIn) == 2: 
                    res.append([f'{self.well_name} #{wn1}',date,0,0,0,"0","0",f"shut in, {comm[wn1]}"])
                    res.append([f'{self.well_name} #{wn2}',date,0,0,0,"0","0",f"shut in, {comm[wn2]}"])  
                
                #no shutins allocate based on avg test for well over avg test all
                #get allocation percent for oil gas water for each well
                if len(shtIn) == 0: 
                    #if date[-2:] != '01': 
                    tests = self.alct_db.copy()
                    tests = tests[self.well_id]['tests'][date[:7]]
                    avgs = {}
                    for w in wn1,wn2,self.twell[date]:
                        for ty in typs:
                            try: avgs[f'{w}_{ty}'] = round(sum(tests[str(w)][ty])/len(tests[str(w)][ty]),2)
                            except (ZeroDivisionError,KeyError):  avgs[f'{w}_{ty}'] = 0
                    
                    short = []
                    for w in [wn1,wn2,self.twell[date]]: 
                        if len(tests[w]['oil']) < 3: short.append(w)
                    
                    for w in short:
                        for ty in typs: 
                            allTests = tests[w][ty]
                            allTests.append(prevAvgs[f'{w}_{ty}'])
                            avgs[f'{w}_{ty}'] = sum(allTests)/len(allTests)
                    
                    avg_tots = {ty: sum(v for k, v in avgs.items() if ty in k) for ty in typs}
                    allcts = {wn1:{},wn2:{},self.twell[date]:{}}
                    for k,v in avgs.items():
                        wn,ty = k.split('_')[0],k.split('_')[1]
                        try: allcts[str(wn)][ty] = v/avg_tots[ty]
                        except ZeroDivisionError: allcts[str(wn)][ty] = 0

                    #get adjusted allocation prct for non test wells
                    del allcts[str(self.twell[date])]

                    allct_tots = {'oil':0,'gas':0,'water':0}
                    for _,v in allcts.items():
                        for ty in typs: allct_tots[ty] += v[ty]

                    adj_allcts = {wn1:{},wn2:{}}
                    for well in allcts:
                        for ty in typs: 
                            try: adj_allcts[well][ty] = allcts[well][ty]/allct_tots[ty]
                            except ZeroDivisionError: adj_allcts[well][ty] = 0
                    res.append([f'{self.well_name} #{wn1}',date,o_lft*adj_allcts[wn1]['oil'],
                                g_lft*adj_allcts[wn1]['gas'],w_lft*adj_allcts[wn1]['water'],"0","0",comm[wn1]])
                    res.append([f'{self.well_name} #{wn2}',date,o_lft*adj_allcts[wn2]['oil'],
                                g_lft*adj_allcts[wn2]['gas'],w_lft*adj_allcts[wn2]['water'],"0","0",comm[wn2]])
                #update allocations
                alct_main = pd.read_json(self.alct_path).to_dict()
                print(f'aclect {alct_main}')
                print(self.twell[date])
                if date[:7] in alct_main[self.well_id]['tests'].keys():
                    for ty in typs: alct_main[self.well_id]['tests'][date[:7]][str(self.twell[date])][ty].append(self.tprod[date][ty])
                else: 
                    alct_main[self.well_id]['tests'][date[:7]] = {int(w): {ty: [] for ty in typs} for w in [wn1, wn2, self.twell[date]]}
                    for ty in typs: alct_main[self.well_id]['tests'][date[:7]][int(self.twell[date])][ty].append(self.tprod[date][ty])
                with open('data/prod/NM/allocations.json','w') as f: json.dump(alct_main,f)
        return res

def generateMnthArray(start_year, end_year):
    date_array = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            first_day = f"{year}-{month:02d}-01"
            last_day = f"{year}-{month:02d}-{calendar.monthrange(year, month)[1]}"
            date_array.append([first_day, last_day])
    return date_array


if __name__ == '__main__':
    fld = Field('SOUTH TEXAS','ST','2024-07-20',None)
    print(fld.IWell.wells)
    #'Pfeiffer-Byrd #1': 33344
    fld.importGasData(33344,'Pfeiffer-Byrd #1')
       
    


    
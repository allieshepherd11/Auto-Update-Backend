import iWell
from datetime import datetime,timedelta
import time
import requests
import os 
from dotenv import load_dotenv
import time
import json
import pandas as pd
#from Tanks import WellBattery,format_save_loads,callable_loads,save_runtickets

class Field():
    def __init__(self,field,abbr,start) -> None:
        self.field = field
        self.abbr = abbr
        self.start = start
        self.calls = 1
        self.since = datetime.strptime(str(start), "%Y-%m-%d").timestamp()
        self.imprtDays = self.dStrs(start,str(datetime.today().date()))

        self.token = self.access()
        w = self.GET_field(self.GET_wellGroups()[field])
        if abbr == "WT": w.update(self.GET_field('2502'))#cc wells
        self.wells = {well:w[well] for well in sorted(w)}
        
    def __repr__(self):
        return '\n'.join([
            f'Field: {self.field}',
            f'User: {self.me()}',
            f'Num Wells: {len(self.wells)}'])
    
    def importData(self):
        since = datetime.strptime(str(self.start), "%Y-%m-%d").timestamp()
        updates = []
        importData = []
        batteries = {}
        runtickets = pd.DataFrame()

        for well,id in self.wells.items():
            if 'Compressor' in well or 'Drip' in well or 'SWD' in well: continue
            print(well)

            #batteries[well],well_tickets=WellBattery(well,id,self.token,self.since).handle()
            batteries[well],well_tickets = self.tank_levels(well,id)
            runtickets=pd.concat([runtickets,well_tickets])
            prod,comms,tp,cp = self.fetch_data(id,since)
            
            for i in prod[:]:
                if i["production_time"] != i["updated_at"] and i["production_time"] < since and i["date"] != str(datetime.today().date()):#gets updated prod, but not today or updates since last import
                    i["Well Name"] = well
                    updates.append(i)
                    prod.remove(i)

            for i in prod[:]:# copy of list
                if i["date"] == str(datetime.today().date()) or i["date"] == str(self.start) or time.mktime(datetime.strptime(i["date"], "%Y-%m-%d").timetuple()) < since: prod.remove(i)
            if prod == []:#needs fix
                importData.append([well,'2023-08-10',0,0,0,"","","No data"])
                continue
            #check if shared battery
            alct_path = f'data\prod\\{self.abbr}\\allocations.json'
            try: alct = pd.read_json(alct_path).to_dict()
            except FileNotFoundError: alct = {'no':0}

            if (id in alct.keys()): 
                sharedBatt = Allocations(self.token,id,prod,comms,alct_path,since,self.imprtDays).allocate()
                for entry in sharedBatt: importData.append(entry)
                continue

            #get list of production time for cp and tp
            cp_times = [cp[i]["updated_at"] for i in range(len(cp))]
            tp_times = [tp[i]["updated_at"] for i in range(len(tp))]

            for i in range(len(prod)):
                date = prod[i]["date"]
                date_2300 = time.mktime(datetime.strptime(date, "%Y-%m-%d").timetuple()) + 82800#11pm on day of production
                #use tp/cp value that is recorded at the end of day
                try:
                    most_recent_cp = min(cp_times, key=lambda x:abs(x-date_2300))
                    for j in cp:
                        if j["updated_at"] == most_recent_cp:
                            cp_value = j["value"]
                            break
                except:#no cp data
                    cp_value = ""
                try:
                    most_recent_tp = min(tp_times, key=lambda x:abs(x-date_2300))
                    for k in tp:
                        if k["updated_at"] == most_recent_tp:
                            tp_value = k["value"]
                            break
                except:#no tp data
                    tp_value = ""

                data = [well,prod[i]["date"],prod[i]["oil"],prod[i]["gas"],prod[i]["water"],tp_value,cp_value]

                for c in range(len(comms)):
                    dt = datetime.fromtimestamp(comms[c]['note_time']).strftime('%Y-%m-%d')
                    if dt == date: 
                        data.append(comms[c]['message'])
                        break
                if len(data) == 7: data.append("")
                importData.append(data)
        
        if self.abbr == 'ST': 
            with open(f"data\prod\ST\\batteries.jsonbatteries.json",'w') as f: json.dump(batteries,f)

        dfimport = pd.DataFrame(data=importData,columns=["Well Name","Date","Oil (BBLS)","Gas (MCF)","Water (BBLS)","TP","CP","Comments"])
        print(f'dfimport {dfimport}')
        dfimport = dfimport.fillna('')
        dfimport = dfimport.sort_values(['Date', 'Well Name'], ascending = [False , True])
        dfimport.Date = pd.to_datetime(dfimport.Date)
        dfimport = dfimport.reset_index(drop=True)

        return dfimport,updates,batteries
    
    def tank_levels(self,well,well_id):
        battery = self.req_wrapper(f"https://api.iwell.info/v1/wells/{well_id}/tanks")
        res = []
        run_tickets = pd.DataFrame()

        for tank in battery:
            readings = self.req_wrapper(f"https://api.iwell.info/v1/tanks/{tank['id']}/readings?since={self.since}")
            info = self.req_wrapper(f"https://api.iwell.info/v1/tanks/{tank['id']}")
           
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
        with open("data\prod\ST/batteries.json","r") as f: data=json.load(f)
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
        with open("equalized.json","w") as f: json.dump(equalized,f)
        
        return

    def callable_load(self):
        with open("data\prod\ST/equalized.json","r") as f: equalized=json.load(f)
        with open("data\prod\ST/batteries.json","r") as f: data=json.load(f)
        load = {'OIL': 190,'WATER':120,'OIL/WATER':120}
        
        res = {}
        for well,tanks in data.items():
            print(well)
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
        print("DF",df)
        df.to_csv('runticketsCurr.csv',index=False)
        return

    def fetch_data(self,id,since):
        prod,comms,tp,cp = None,None,None,None
                
        try:
            prod = self.GET_wellProduction(id,since)
            comms = self.GET_wellComments(id,since)
            tp = self.GET_wellFieldValue(id,607,since)
            cp = self.GET_wellFieldValue(id,1415,since)
        except requests.exceptions.ConnectionError as e: 
            print('connection error')
            time.sleep(10);print('trying again..\n')
            return self.fetch_data(id,since)
        return prod,comms,tp,cp
    
    def req_wrapper(self,url):
        try: 
            x = requests.get(url,headers={'Authorization': f'Bearer {self.token}'})
        except requests.exceptions.ConnectionError:
            print('connection error')
            time.sleep(10);print('trying again..\n')
            return self.req_wrapper(url) 
        return x.json()['data']
    
    def access(self):
        load_dotenv()
        body = {
            "grant_type": "password",
            "client_id": os.getenv('client_id'),
            "client_secret": os.getenv('client_secret'),
            "username": os.getenv('email'),
            "password": os.getenv('password')
        }
        r=requests.post('https://api.iwell.info/v1/oauth2/access-token', headers={"content-type":"application/json"}, json = body); self.handleCall()
        return(r.json()['access_token'])

    def me(self):
        x = requests.get('https://api.iwell.info/v1/me', headers={'Authorization': f'Bearer {self.token}'})
        self.handleCall()
        return f'{x.json()["data"]["name"]}'

    def GET_wellGroups(self):
        group_dict = {}
        x = requests.get('https://api.iwell.info/v1/well-groups', headers={'Authorization': f'Bearer {self.token}'}); self.handleCall()
        data = x.json()['data']
        [group_dict.update({i['name']: i['id']}) for i in data]
        #print("well group:",group_dict)
        return(group_dict)

    def GET_field(self, fieldID):
        well_dict = {}
        x = requests.get(f'https://api.iwell.info/v1/well-groups/{fieldID}/wells', headers={'Authorization': f'Bearer {self.token}'}); self.handleCall()
        data = x.json()['data']   
        [well_dict.update({i['name']: i['id']}) for i in data] 
        return(well_dict)

    def GET_wellProduction(self, well_id,time_since):
        x = requests.get(f'https://api.iwell.info/v1/wells/{well_id}/production?&since={time_since}', headers={'Authorization': f'Bearer {self.token}'})
        self.handleCall()
        prod_data = []
        try:
            data = x.json()['data']   
            for i in data:
                prod_data.append(i)
            return prod_data
        except:
            return prod_data

    def GET_wellFields(self, well_id):
        x = requests.get(f'https://api.iwell.info/v1/wells/{well_id}/fields', headers={'Authorization': f'Bearer {self.token}'}); self.handleCall()
        data = x.json()['data']
        for i in data:
            print(f"{i}\n")

    def GET_wellFieldValue(self,well_id,field_id,time_since):
        x = requests.get(f'https://api.iwell.info/v1/wells/{well_id}/fields/{field_id}/values?since={time_since}', headers={'Authorization': f'Bearer {self.token}'})
        self.handleCall()
        field_value = []

        data = x.json()['data']
        for i in data:
            field_value.append(i)
        return field_value

    def GET_wellComments(self, well_id,time_since):#lists from past to present
        x = requests.get(f'https://api.iwell.info/v1/wells/{well_id}/notes?since={time_since}', headers={'Authorization': f'Bearer {self.token}'})
        self.handleCall()
        data = x.json()
        if 'data' in data.keys(): return data['data']
        return []

    def GET_tanks(self):
        x = requests.get('https://api.iwell.info/v1/tanks', headers={'Authorization': f'Bearer {self.token}'}); self.handleCall()
        data = x.json()['data']
        print(f' data {data}')
        df = pd.DataFrame(data)
        df.to_csv('tanks.csv',index=False)

    def GET_tankReading(self,id,since=''):
        x = requests.get(f'https://api.iwell.info/v1/tanks/{id}/readings?since={since}', headers={'Authorization': f'Bearer {self.token}'})
        self.handleCall()
        data = x.json()['data']
        return data

    def GET_runTicket(self,tankID,readingID):
        x = requests.get(f'https://api.iwell.info/v1/tanks/{tankID}/readings/{readingID}/run-tickets', headers={'Authorization': f'Bearer {self.token}'})
        self.handleCall()
        data = x.json()['data']
        return data

    def POST_tankReading(self,tankID,payload):
        payload = json.dumps(payload)
        response = requests.post(f'https://api.iwell.info/v1/tanks/{tankID}/readings',data=payload ,headers={'Authorization': f'Bearer {self.token}'})
        print(response)
        return

    def GET_wellTests(self,wellID):
        x = requests.get(f'https://api.iwell.info/v1/wells/{wellID}/well-tests', headers={'Authorization': f'Bearer {self.token}'}); self.handleCall()
        data = x.json()
        print(data)
        return data

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

    def handleCall(self):
        self.calls += 1
        if self.calls >= 295: self.calls = 0; print('sleep'); time.sleep(60)
    
    def format_save_loads(self):
        with open("data\prod\ST\loads.json","r") as f: data=json.load(f)
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


class Allocations():
    def __init__(self,token,well_id,prod,comms,alct_path,since,imprtDays) -> None:
        self.well_id = well_id
        self.prod = prod
        self.comms = comms
        self.alct_path = alct_path
        self.alct_db = pd.read_json(alct_path).to_dict()
        self.well_name = self.alct_db[well_id]['name']
        try:
            tnum = iWell.GET_wellFieldValue(token,well_id,'805',since)
            testprod = [iWell.GET_wellFieldValue(token,well_id,key,since)  for key in [806,855,807]]#oil,gas,water
        except requests.exceptions.ConnectionError as e: 
            print(f'API Limit on {self.well_name}');time.sleep(61)
            tnum = iWell.GET_wellFieldValue(token,well_id,'805',since)
            testprod = [iWell.GET_wellFieldValue(token,well_id,key,since)  for key in [806,855,807]]

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
        print(f'test wells {self.twell}')

    def lstMnthAvg(self,date,wn1,wn2) -> dict:
        lst_mnth = int(datetime.strptime(date,'%Y-%m-%d').timestamp()) - 60*60*24*int(date[-2:])
        lst_mnth = datetime.utcfromtimestamp(lst_mnth).strftime('%Y-%m-%d')[:7]
        tests = self.alct_db[self.well_id]['tests'][lst_mnth]
        print(f'tests {tests}')
        avgs = {f'{w}_{ty}':round(sum(tests[str(w)][ty])/len(tests[str(w)][ty]),2) 
                for w in [wn1,wn2,self.twell[date]] for ty in ['oil','gas','water']}
        
        #res = {w:{'oil':[],'gas':[],'water':[]} for w in [wn1,wn2,self.twell[date]]}
        #for k,v in avgs.items():
        #    unpack = k.split('_')
        #    res[int(unpack[0])][unpack[1]].append(v)
        #print(f'res {res}')
        #self.alct_db[self.well_id]['tests'][date[:7]] = res
        #with open('data\prod\\NM\\allocations.json','w') as f:
        #    json.dump(self.alct_db,f)
        return  avgs

    def assignComm(self,comm,commtw,*wells):
        print(f'comm {comm}')

        splt_comm = {w:'' for w in wells}
        print(f'spl {splt_comm}')
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
            if date == '2023-08-20':continue
            print(f'date {date}')
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
                    print(f'key errr')
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
                    print(f'pre avgs {prevAvgs}')
                    if date[-2:] != '01': 
                        tests = self.alct_db.copy()
                        tests = tests[self.well_id]['tests'][date[:7]]
                        avgs = {}
                        for w in wn1,wn2,self.twell[date]:
                            for ty in typs:
                                try: avgs[f'{w}_{ty}'] = round(sum(tests[str(w)][ty])/len(tests[str(w)][ty]),2)
                                except ZeroDivisionError:  avgs[f'{w}_{ty}'] = 0
                        
                        short = []
                        for w in [wn1,wn2,self.twell[date]]: 
                            if len(tests[w]['oil']) < 3: short.append(w)
                        
                        for w in short:
                            for ty in typs: 
                                allTests = tests[w][ty]
                                allTests.append(prevAvgs[f'{w}_{ty}'])
                                avgs[f'{w}_{ty}'] = sum(allTests)/len(allTests)
                                print(f"avgs[f'{w}_{ty}'] {avgs[f'{w}_{ty}']}")
                    
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
                try: 
                    for ty in typs: alct_main[self.well_id]['tests'][date[:7]][str(self.twell[date])][ty].append(self.tprod[date][ty])
                except KeyError: 
                    alct_main[self.well_id]['tests'][date[:7]] = {}
                    for ty in typs: alct_main[self.well_id]['tests'][date[:7]][int(self.twell[date])][ty].append(self.tprod[date][ty])
                with open('data\prod\\NM\\allocations.json','w') as f: json.dump(alct_main,f)
        return res

if __name__ == '__main__':
    start = '2024-01-07'
    fld = Field('SOUTH TEXAS','ST',start)
    fld.importData()
    exit()
    dfimport,updates = fld.importData()


    


    
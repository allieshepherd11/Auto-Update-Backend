import iWell
from datetime import datetime,timedelta
import time
import requests
import os 
from dotenv import load_dotenv
import time
import json
import pandas as pd


def nw():
    field = 'New Mexico'
    TOKEN = iWell.init()
    iWell.me(TOKEN)
    wellGroups = iWell.well_group(TOKEN)
    
    nw = iWell.single_well_group(TOKEN,wellGroups[field])
    since = 1689638400#7/18
    start = since

    updates = []
    importData = []
    print(sorted(nw))
    bats = ['Abenaki 10 State #2 & #3',
    'Beams 15 State #2 & 4',    
    'Henry 24 #1',
    'Paddy 15 State #1', 
    'Paddy 18 State #1 & #3',
    'Paddy 19 State #1 #4 #5',
    'Paddy 19 State #2 & #3',
    'Raider 9 St. #1, #3']
    for well in sorted(bats):
        test = iWell.GETwellTests(TOKEN,nw[well])
        print(f'{well} , id: {nw[well]}')
    exit()    

    #missing 

    #shared batteries

    #Abenaki 10 State #2 & #3
    #Beams 15 State #2 & 4    called Beams 15 State # on iwell
    #Henry 24 #1
    #Paddy 15 #1             gives 1,2,3
    #Paddy 18 State #1 & #3
    #Paddy 19 State #1 #4 #5
    #Paddy 19 State #2 & #3
    #Raider 9 St. #1, #3     test # says 2 and 3 but seems to be for 1 and 3
    ['Abenaki 10 State #2 & #3',
    'Beams 15 State #2 & 4',    
    'Henry 24 #1',
    'Paddy 15 #1            ', 
    'Paddy 18 State #1 & #3',
    'Paddy 19 State #1 #4 #5',
    'Paddy 19 State #2 & #3',
    'Raider 9 St. #1, #3 ']


class Field():
    def __init__(self, field,abbr,start) -> None:
        self.field = field
        self.abbr = abbr
        self.start = start
        self.since = datetime.strptime(str(start), "%Y-%m-%d").timestamp()
        self.imprtDays = self.dStrs(start,str(datetime.today().date()))
        self.token = self.access()
        w = self.GET_field(self.GET_wellGroups()[self.field]) 
        self.wells = {well:w[well] for well in sorted(w) }
        self.calls = 3
        
    def __repr__(self):
        return '\n'.join([
            f'Field: {self.field}',
            f'User: {self.me()}',
            f'Num Wells: {len(self.wells)}'])
    
    def importData(self):
        since = datetime.strptime(str(self.start), "%Y-%m-%d").timestamp()
        updates = []
        importData = []
        for well,id in self.wells.items():
            if 'Compressor' in well or 'Drip' in well: continue
            try:
                self.handleCall()
                prod = self.GET_wellProduction(id,since); self.handleCall()
                comms = self.GET_wellComments(id,since); self.handleCall()
                tp = self.GET_wellFieldValue(id,607,since); self.handleCall()
                cp = self.GET_wellFieldValue(id,1415,since)
                print(well)
            except Exception as e: print(e,"no data for",well); continue

            for i in prod[:]:
                if i["production_time"] != i["updated_at"] and i["production_time"] < since and i["date"] != str(datetime.today().date()):#gets updated prod, but not today or updates since last import
                    i["Well Name"] = well
                    updates.append(i)
                    prod.remove(i)

            for i in prod[:]:# copy of list
                if i["date"] == str(datetime.today().date()) or i["date"] == str(self.start) or time.mktime(datetime.strptime(i["date"], "%Y-%m-%d").timetuple()) < since: prod.remove(i)
            
            #check if shared battery
            alct_path = f'data\prod\\{self.abbr}\\allocations.json'
            try: alct = pd.read_json(alct_path).to_dict()
            except FileNotFoundError: alct = {'no':0}

            if (id in alct.keys()): 
                for entry in self.allocation(id,prod,comms,alct,alct_path): importData.append(entry)
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
        dfimport = pd.DataFrame(data=importData,columns=["Well Name","Date","Oil (BBLS)","Gas (MCF)","Water (BBLS)","TP","CP","Comments"])
        dfimport = dfimport.fillna('')
        dfimport = dfimport.sort_values(['Date', 'Well Name'], ascending = [False , True])
        dfimport.Date = pd.to_datetime(dfimport.Date)
        dfimport = dfimport.reset_index(drop=True)

        return dfimport,updates
    
    def allocation(self,id,prod,comms,alct,alct_path) -> list:#makes 4 api calls
        print(f'id {id}')
        well_name = alct[id]['name']
                
        tnum = self.GET_wellFieldValue(id,'805',self.since); self.handleCall()
        testprod = [self.GET_wellFieldValue(id,key,self.since)  for key in [806,855,807]]#oil,gas,water
        
        twell = {k:None for k in self.imprtDays}
        
        for test in tnum: twell[datetime.fromtimestamp(test['reading_time']).strftime('%Y-%m-%d')] = int(test['value'])
        tprod = {k:{} for k in self.imprtDays}
        for comm in comms:
            dstr = datetime.fromtimestamp(comm['note_time']).strftime('%Y-%m-%d')
            if dstr in tprod.keys(): tprod[dstr]['comm'] = comm['message']

        for i in range(len(testprod)):
            for rd in testprod[i]:
                dstr = datetime.fromtimestamp(rd['reading_time']).strftime('%Y-%m-%d')
                if dstr in self.imprtDays: tprod[dstr][['oil','gas','water'][i]] = float(rd['value'])
        
        for day,prd in tprod.items():
            misses = [i for i in ['oil','gas','water'] if i not in prd.keys()]
            for miss in misses: tprod[day][miss] = 0#tests[id][float(twell[day])][miss]
        
        typs = ['oil','gas','water']
        res = []
        for day in prod:
            date = day['date']
            comm = tprod[date]['comm'] if 'comm' in tprod[date].keys() else ""

            shtIn = alct[id]['shutIn'][date] if date in alct[id]['shutIn'].keys() else []
            cb = alct[id]['wells'][:]
            if twell[date] in cb: cb.remove(twell[date])

            if twell[date] is None or twell[date] not in alct[id]['wells']:#no test well
                if len(shtIn) == 1 and len(cb) == 2:
                    wn1 = cb.pop(); wn2 = cb.pop()
                    wellNum = wn2 if int(wn1) in shtIn else wn1
                    res.append([f'{well_name} #{wellNum}',date,day['oil'],day['gas'],day['water'],"0","0",comm])
                    res.append([f'{well_name} #{shtIn[0]}',date,0,0,0,"0","0","shut in"]);continue
                else: twell[date] = cb[0];comm = f'{comm} no test well set, {cb[0]} used as test'
            
            lft = [float(day[ty]) - tprod[date][ty] for ty in typs];lft = [max(0, val) for val in lft]
            o_lft,g_lft,w_lft = lft[0],lft[1],lft[2]

            res.append([f'{well_name} #{twell[date]}',date,tprod[date]['oil'],tprod[date]['gas'],tprod[date]['water'],"0","0",comm])

            if len(alct[id]['wells']) == 2:
                wellNum = cb.pop()
                #["Well Name","Date","Oil (BBLS)","Gas (MCF)","Water (BBLS)","TP","CP","Comments"]
                res.append([f'{well_name} #{wellNum}',date, o_lft, g_lft, w_lft,"0","0",comm])
            if len(alct[id]['wells']) == 3:
                wn1 = cb.pop(); wn2 = cb.pop(); tests = alct[id]['tests'][date[:7]]
                if twell[date] in shtIn: exit(print(f'Error: test well {twell[date]} is shut in'))
                if len(shtIn) == 1:
                    wellNum = wn2 if int(wn1) in shtIn else wn1
                    res.append([f'{well_name} #{wellNum}',date, o_lft,g_lft, w_lft,"0","0",comm])
                    res.append([f'{well_name} #{shtIn[0]}',date,0,0,0,"0","0","shut in"])
                    
                if len(shtIn) == 2: 
                    res.append([f'{well_name} #{wn1}',date,0,0,0,"0","0","shut in"])
                    res.append([f'{well_name} #{wn2}',date,0,0,0,"0","0","shut in"])  
                
                #no shutins allocate based on avg test for well over avg test all
                #get allocation percent for oil gas water for each well
                if len(shtIn) == 0:
                    avgs = {f'{w}_{ty}':round(sum(tests[str(w)][ty])/len(tests[str(w)][ty]),2) for w in [wn1,wn2,twell[date]] for ty in typs}
                    avg_tots = {ty: sum(v for k, v in avgs.items() if ty in k) for ty in typs}
                    allcts = {wn1:{},wn2:{},twell[date]:{}}
                    for k,v in avgs.items():
                        wn,ty = k.split('_')[0],k.split('_')[1]
                        try: allcts[int(wn)][ty] = v/avg_tots[ty]
                        except ZeroDivisionError: allcts[int(wn)][ty] = 0
                    #get adjusted allocation prct for non test wells
                    del allcts[int(twell[date])]

                    allct_tots = {'oil':0,'gas':0,'water':0}
                    for _,v in allcts.items():
                        for ty in typs: allct_tots[ty] += v[ty]

                    adj_allcts = {wn1:{},wn2:{}}
                    for well in allcts:
                        for ty in typs: 
                            try: adj_allcts[well][ty] = allcts[well][ty]/allct_tots[ty]
                            except ZeroDivisionError: adj_allcts[well][ty] = 0
                    res.append([f'{well_name} #{wn1}',date,o_lft*adj_allcts[wn1]['oil'],
                                g_lft*adj_allcts[wn1]['gas'],w_lft*adj_allcts[wn1]['water'],"0","0",comm])
                    res.append([f'{well_name} #{wn2}',date,o_lft*adj_allcts[wn2]['oil'],
                                g_lft*adj_allcts[wn2]['gas'],w_lft*adj_allcts[wn2]['water'],"0","0",comm])
                
                #update allocations
                #for ty in typs:
                #    tests[str(twell[date])][ty].append(tprod[date][ty])
                #
                #
                #with open('tst.json','w') as f:
                #    json.dump(alct,f)
        
        return res
        
    def access(self):
        load_dotenv()
        body = {
            "grant_type": "password",
            "client_id": os.getenv('client_id'),
            "client_secret": os.getenv('client_secret'),
            "username": os.getenv('email'),
            "password": os.getenv('password')
        }
        r=requests.post('https://api.iwell.info/v1/oauth2/access-token', headers={"content-type":"application/json"}, json = body)
        return(r.json()['access_token'])

    def me(self):
        x = requests.get('https://api.iwell.info/v1/me', headers={'Authorization': f'Bearer {self.token}'})
        return f'{x.json()["data"]["name"]}'

    def GET_wellGroups(self):
        group_dict = {}
        x = requests.get('https://api.iwell.info/v1/well-groups', headers={'Authorization': f'Bearer {self.token}'})
        data = x.json()['data']
        [group_dict.update({i['name']: i['id']}) for i in data]
        #print("well group:",group_dict)
        return(group_dict)

    def GET_field(self, fieldID):
        well_dict = {}
        x = requests.get(f'https://api.iwell.info/v1/well-groups/{fieldID}/wells', headers={'Authorization': f'Bearer {self.token}'})
        data = x.json()['data']   
        [well_dict.update({i['name']: i['id']}) for i in data] 
        return(well_dict)

    def GET_wellProduction(self, well_id,time_since):
        x = requests.get(f'https://api.iwell.info/v1/wells/{well_id}/production?&since={time_since}', headers={'Authorization': f'Bearer {self.token}'})
        prod_data = []
        try:
            data = x.json()['data']   
            for i in data:
                prod_data.append(i)
            return prod_data
        except:
            return prod_data

    def GET_wellFields(self, well_id):
        x = requests.get(f'https://api.iwell.info/v1/wells/{well_id}/fields', headers={'Authorization': f'Bearer {self.token}'})
        data = x.json()['data']
        for i in data:
            print(f"{i}\n")

    def GET_wellFieldValue(self,well_id,field_id,time_since):
        self.handleCall()
        x = requests.get(f'https://api.iwell.info/v1/wells/{well_id}/fields/{field_id}/values?since={time_since}', headers={'Authorization': f'Bearer {self.token}'})
        field_value = []
        data = x.json()['data']
        for i in data:
            field_value.append(i)
        return field_value

    def GET_wellComments(self, well_id,time_since):#lists from past to present
        x = requests.get(f'https://api.iwell.info/v1/wells/{well_id}/notes?since={time_since}', headers={'Authorization': f'Bearer {self.token}'})
        data = x.json()
        if 'data' in data.keys(): return data['data']
        return []

    def GET_tanks(self):
        x = requests.get('https://api.iwell.info/v1/tanks', headers={'Authorization': f'Bearer {self.token}'})
        data = x.json()['data']
        print(f' data {data}')
        df = pd.DataFrame(data)
        df.to_csv('tanks.csv',index=False)

    def GET_tankReading(self,id,since=''):
        x = requests.get(f'https://api.iwell.info/v1/tanks/{id}/readings?since={since}', headers={'Authorization': f'Bearer {self.token}'})
        data = x.json()['data']
        return data

    def GET_runTicket(self,tankID,readingID):
        x = requests.get(f'https://api.iwell.info/v1/tanks/{tankID}/readings/{readingID}/run-tickets', headers={'Authorization': f'Bearer {self.token}'})
        data = x.json()['data']
        return data

    def POST_tankReading(self,tankID,payload):
        payload = json.dumps(payload)
        response = requests.post(f'https://api.iwell.info/v1/tanks/{tankID}/readings',data=payload ,headers={'Authorization': f'Bearer {self.token}'})
        print(response)
        return

    def GET_wellTests(self,wellID):
        x = requests.get(f'https://api.iwell.info/v1/wells/{wellID}/well-tests', headers={'Authorization': f'Bearer {self.token}'})
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
        if self.calls >= 23: self.calls = 0; print('sleep'); time.sleep(60)

#if __name__ == '__main__':
#    #df = pd.read_csv('data\prod\GC\data.csv')11441
#    start = '2023-07-16'
#    fld = Field('New Mexico','NM',start)
#    print(fld)
#    print(fld.wells)
#    dfimport,updates = fld.importData()
    


    
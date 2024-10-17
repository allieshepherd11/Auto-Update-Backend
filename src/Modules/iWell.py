import pandas as pd
from datetime import datetime
import requests
import time
import os 
from dotenv import load_dotenv
import time
import json
from collections import defaultdict


def method_wrapper(calls):
    def _handle_errors(foo):
        def wrapper(self,*args, **kwargs):
            setattr(self, calls, getattr(self, calls, 0) + 1)
            while True:
                try:
                    return foo(self, *args, **kwargs)
                except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
                    print("Connection Error")
                    time.sleep(10)
                    print('Retrying...')
        return wrapper
    return _handle_errors

def wrap_methods(calls):
    def decorator(cls):
        for name, method in vars(cls).items():
            if callable(method):
                setattr(cls, name, method_wrapper(calls)(method))
        return cls
    return decorator

@wrap_methods('calls')
class IWell:
    def __init__(self,field,abbr,since,dateRange=None) -> None:
        self.since = since
        self.dateRange = dateRange
        self.abbr = abbr
        self.calls = 0
        self.token = self.access()
        w = self.GET_field(self.GET_wellGroups()[field])
        
        if self.abbr == "WT": w.update(self.GET_field('2502'))#cc wells
        self.wells = {well:w[well] for well in sorted(w)}

        if dateRange: self.filter = f'start={dateRange[0]}&end={dateRange[1]}'
        else: self.filter = f'since={self.since}'

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

    def handleCall(self):
        self.calls += 1
        if self.calls >= 295: self.calls = 0; print('sleep'); time.sleep(60)

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

    def GET_wellProduction(self, well_id):
        x = requests.get(f'https://api.iwell.info/v1/wells/{well_id}/production?{self.filter}', headers={'Authorization': f'Bearer {self.token}'})
        if x.status_code == 200:
            x = x.json()
            if 'data' in x.keys():
                return x['data']
        return []

    def GET_wellFields(self, well_id):
        x = requests.get(f'https://api.iwell.info/v1/wells/{well_id}/fields?{self.filter}', headers={'Authorization': f'Bearer {self.token}'})
        return x.json()['data']

    def GET_wellFieldValue(self,well_id,field_id,dateRange=None):
        x = requests.get(f'https://api.iwell.info/v1/wells/{well_id}/fields/{field_id}/values?{self.filter}', headers={'Authorization': f'Bearer {self.token}'})
        if x.status_code == 404:
            return [{"updated_at":-1,"values":-1}]
        return x.json()['data']

    def GET_wellComments(self, well_id):#lists from past to present
        x = requests.get(f'https://api.iwell.info/v1/wells/{well_id}/notes?{self.filter}', headers={'Authorization': f'Bearer {self.token}'})
        data = x.json()
        if 'data' in data.keys(): return data['data']
        return []

    def GET_tanks(self):
        x = requests.get('https://api.iwell.info/v1/tanks', headers={'Authorization': f'Bearer {self.token}'})
        data = x.json()['data']
        print(f' data {data}')
        df = pd.DataFrame(data)
        df.to_csv('tanks.csv',index=False)

    def GET(self,url):
        x = requests.get(url, headers={'Authorization': f'Bearer {self.token}'})
        return x.json()['data']

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

    def GET_wellMeters(self,wellID):
        x = requests.get(f'https://api.iwell.info/v1/wells/{wellID}/meters?since={since}', headers={'Authorization': f'Bearer {self.token}'})
        data = x.json()['data']
        return data
    
    def GET_wellMetersReadings(self,wellID,meterID):
        x = requests.get(f'https://api.iwell.info/v1/wells/{wellID}/meters/{meterID}/readings?since={since}', headers={'Authorization': f'Bearer {self.token}'})
        data = x.json()['data']
        return data
    
def fetch_historical_data():
    since = datetime.strptime(str('2024-5-01'), "%Y-%m-%d").timestamp()
    iw = IWell(field='SOUTH TEXAS',abbr='ST',since=since)

    mnths = [
        ['2023-06-01','2023-06-30'],
        ['2023-07-01','2023-07-31'],
        ['2023-08-01','2023-08-31'],
        ['2023-09-01','2023-09-30'],
        ['2023-10-01','2023-10-31'],
        ['2023-11-01','2023-11-30'],
        ['2023-12-01','2023-12-31'],
        ['2024-01-01','2024-01-31'],
        ['2024-02-01','2024-02-28'],
        ['2024-03-01','2024-03-31'],
        ['2024-04-01','2024-04-30'],
        ['2024-05-01','2024-05-31'],
    ]
    with open('linePressuresHistory.json', 'r') as f:
        res = json.load(f)
    for well,wellId in iw.wells.items():
        print(well)
        for mnth in mnths:
            res[well]['Sales Pressure'].extend(iw.GET_wellFieldValue(wellId,4088,dateRange=mnth))
            res[well]['Flow Rate Sales'].extend(iw.GET_wellFieldValue(wellId,4091,dateRange=mnth))
            res[well]['Flow Rate Flare'].extend(iw.GET_wellFieldValue(wellId,4096,dateRange=mnth))
    with open('linePressuresHistory.json', 'w') as f:
        json.dump(res,f)
    return

if __name__ == "__main__":
    since = datetime.strptime(str('2024-8-01'), "%Y-%m-%d").timestamp()
    iw = IWell('','',since)
       

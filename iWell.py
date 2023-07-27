import pandas as pd
from datetime import datetime
import requests
import time
import os 
from dotenv import load_dotenv
import time
import json

load_dotenv()
client_id = os.getenv('client_id')
client_secret = os.getenv('client_secret')
username = os.getenv('email')
password = os.getenv('password')

def init():
    body = {
        "grant_type": "password",
        "client_id": client_id,
        "client_secret": client_secret,
        "username": username,
        "password": password
    }
    r=requests.post('https://api.iwell.info/v1/oauth2/access-token', headers={"content-type":"application/json"}, json = body)
    return(r.json()['access_token'])

def me(token):
    x = requests.get('https://api.iwell.info/v1/me', headers={'Authorization': f'Bearer {token}'})
    print(f'The current user is {x.json()["data"]["name"]}')

def wells(token):
    x = requests.get('https://api.iwell.info/v1/wells', headers={'Authorization': f'Bearer {token}'})
    data = x.json()['data']
    print(data[0])

def well_group(token):
    group_dict = {}
    x = requests.get('https://api.iwell.info/v1/well-groups', headers={'Authorization': f'Bearer {token}'})
    data = x.json()['data']
    [group_dict.update({i['name']: i['id']}) for i in data]
    #print("well group:",group_dict)
    return(group_dict)

def single_well_group(token, group_id):
    well_dict = {}
    x = requests.get(f'https://api.iwell.info/v1/well-groups/{group_id}/wells', headers={'Authorization': f'Bearer {token}'})
    data = x.json()['data']   
    [well_dict.update({i['name']: i['id']}) for i in data] 
    return(well_dict)

def well_production(token, well_id,time_since,cnt=[]):#time_since = 0 gives last 30 days
    cnt.append(0)
    x = requests.get(f'https://api.iwell.info/v1/wells/{well_id}/production?&since={time_since}', headers={'Authorization': f'Bearer {token}'})
    prod_data = []
    try:
        data = x.json()['data']   
        for i in data:
            prod_data.append(i)
        return prod_data,cnt,x
    except:
        return prod_data,cnt,x

def well_fields(token, well_id):
    x = requests.get(f'https://api.iwell.info/v1/wells/{well_id}/fields', headers={'Authorization': f'Bearer {token}'})
    data = x.json()['data']
    for i in data:
        print(f"{i}\n")

def well_field_value(token,well_id,field_id,time_since):
     x = requests.get(f'https://api.iwell.info/v1/wells/{well_id}/fields/{field_id}/values?since={time_since}', headers={'Authorization': f'Bearer {token}'})
     field_value = []
     data = x.json()['data']
     for i in data:
        field_value.append(i)
     return field_value

def well_comments(token, well_id,time_since):#lists from past to present
    x = requests.get(f'https://api.iwell.info/v1/wells/{well_id}/notes?since={time_since}', headers={'Authorization': f'Bearer {token}'})
    data = x.json()
    print(f'comment data: {data}' )
    if 'data' in data.keys(): return data['data']
    return []

def GET_tanks(token):
    x = requests.get('https://api.iwell.info/v1/tanks', headers={'Authorization': f'Bearer {token}'})
    data = x.json()['data']
    print(f' data {data}')
    df = pd.DataFrame(data)
    df.to_csv('tanks.csv',index=False)

def GET_tank_reading(token,id,since=''):
    x = requests.get(f'https://api.iwell.info/v1/tanks/{id}/readings?since={since}', headers={'Authorization': f'Bearer {token}'})
    data = x.json()['data']
    return data

def GET_run_ticket(token,tankID,readingID):
    x = requests.get(f'https://api.iwell.info/v1/tanks/{tankID}/readings/{readingID}/run-tickets', headers={'Authorization': f'Bearer {token}'})
    data = x.json()['data']
    return data

def POST_tank_reading(token,tankID,payload):
    payload = json.dumps(payload)
    response = requests.post(f'https://api.iwell.info/v1/tanks/{tankID}/readings',data=payload ,headers={'Authorization': f'Bearer {token}'})
    print(response)
    return

def GETwellTests(token,wellID):
    x = requests.get(f'https://api.iwell.info/v1/wells/{wellID}/well-tests', headers={'Authorization': f'Bearer {token}'})
    data = x.json()
    print(data)
    return data

def GETwellTanks(token,wellID):
    x = requests.get(f'https://api.iwell.info/v1/wells/{wellID}/tanks', headers={'Authorization': f'Bearer {token}'})
    data = x.json()['data']
    return data
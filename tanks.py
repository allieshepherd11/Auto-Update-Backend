import pandas as pd
import requests
from dotenv import load_dotenv
import datetime
import os 
from iWellApi import init, me, GET_tank_reading, GET_run_ticket, POST_tank_reading
import plotly.graph_objects as go
import time
import json

def plot(x,y,ids,title):
    trace = go.Scatter(
        x=x,
        y=y,
        mode='lines+markers',  
        marker=dict(
            size=10,
            color='green'
        ),
        text=ids
    )
    layout = go.Layout(
        title=title,
        xaxis=dict(title='Date'),
        yaxis=dict(title='Tank Reading [ft]')
    )   
    fig = go.Figure(data=[trace], layout=layout)

    fig.show()

def rdTank(tankID,tankName,since=''):
    data = GET_tank_reading(token,tankID,since)
    #print(f'data : {data}')
    res = {'date':[],'reading':[],'id':[],'exct reading': []}
    r = []
    print(tankID)
    for i in data:
        temp = {}
        print(i)
        exit()
        ft = round(int(i["top_feet"]) + int(i["top_inches"])/12,3)
        rstr = f"{i['top_feet']}' {i['top_inches']}''"
        dt = datetime.datetime.fromtimestamp(i['reading_time'])
        #res["reading"].append(ft)json format
        #res['exct reading'].append(rstr)
        #res['date'].append(dt.strftime('%m-%d-%Y'))
        #res['id'].append(i['id'])
        temp["reading"] = ft
        temp["exct reading"] = rstr
        temp["date"] = dt.strftime('%m-%d-%Y')
        temp["id"] = i['id']
        temp['unix'] = i['reading_time']
        r.append(temp)

    #print(f'res : {res}')
    #plot(res["date"],res["reading"],res['id'],'Parkway #1 271278 Remote')
    #resdf = pd.DataFrame(res)
    #print(f'\n {res}')
    #resdf.to_json(f'db\\tanks\\readings{tankName}.json',orient='records')

    return r

def post_reading(tankID,remoteID=None):
    rdID = remoteID
    if rdID is None: rdID = tankID
    data = GET_tank_reading(token,rdID,since=1688048502)
    if len(data) > 1:#fix
        print('wknd')
        exit()
    data = data[0]
    del data['id']
    del data['updated_at']
    del data['updated_by']
    #if tank type == oil:
    for key,_ in data.items():
        if 'cut' in key:
            data[key] = None
    ##
    data['reading_time'] = 1688122800
    print(f'data: {data}')
    POST_tank_reading(token,tankID,data)

def handleWell(tanks):
    print(f'tanks : {tanks}')
    remoteID = [tanks[tank] if 'Rem' in tank else None for tank in tanks.keys()].pop()
    print(remoteID)
    remote_readings = GET_tank_reading(token,remoteID)
    
    #get rem


if __name__ == "__main__":
    token = init()
    me(token)
    tankIDs = {"Parkway #1":{
        "equalized": ['10911','10910'],
        "271278" : "10911",
        "271277" : "10910",
        "271276" : "10909",
        "271275" : "10908",
        "271278 Remote" : "21942",
        }
    }
    for well in tankIDs:
        handleWell(tankIDs[well])
    exit()






    exit()
    tanks = {}
    lst_date = None
    lst_rdID = None
    for well in tankIDs.keys():
        for name,id in tankIDs[well].items():
            if 'mot' not in name and 'eq' not in name:
                tank = rdTank(id,tankName=None)
                print(tank)
                tanks[name] = tank
                lst_date = tank[-1]['unix']
                lst_rdID = tank[-1]['id']
    print(f'tanks : {tanks}\n')
    print(f'last reading at : {lst_date}')
    last_rd = tanks['271278'][-1]
    curr_reading = rdTank("21942","271278 Remote",'1687960800')
    print(f'curr : {curr_reading}')
    print(f'lst reading : {last_rd}')
    if len(curr_reading) > 1: 
        print('weekend')
        exit()#fix

    #{'id': 22754028, 'reading_time': 1685499090, 'top_feet': 7, 'top_inches': 4, 
    # 'cut_feet': 0, 'cut_inches': 0, 'previous_top_feet': 5, 'previous_top_inches': 7,
    # 'previous_cut_feet': 0, 'previous_cut_inches': 0, 'updated_at': 1685500445, 'updated_by': 6687}

    

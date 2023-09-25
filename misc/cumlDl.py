import os
import pandas as pd

path = 'C:\\Users\\plaisancem\\Documents\\well_files'

stpoints = {
    'RAB #2':{'OH':7577,'ST01':7694,'ST02':9296,'ST03':9375},
    'RAB #3':{'OH':7724,'ST01':10142,'ST02':7724,'ST03':10518,'ST04':10047},
    'Marrs #1':{'OH':7795,'ST01':9867,'ST03':8110},
    'Bruce Weaver #2 RE': {'OH':6330,'ST01':5550,'ST02':6266,'ST03':5732,'ST04':5856},
    'Jic Buda #1':{'OH':7356,'ST01':7200},
    'Sansom #1':{'OH':7856,'ST01':7260},
    'Fatheree #1':{'OH':7440,'ST01':5616,'ST02':5932},
    'Drinkard #1':{'OH':6557,'ST01':6930,'ST02':5709,'ST03':5929,'ST04':5804},
    'Balfour #1':{'OH':7792,'ST01':15032},
    'Little 179 #1':{'ST01':5506,'ST02':5901,'ST03':6122},
    'Burns Ranch 2 #1':{'OH':7646,'ST01':6824,'ST02':6730,'ST03':1106},
    'Burns Ranch GT #1':{'ST04':7423},
    'Dial #1 ST':{'OH':6166,'ST01':5287,'ST02':5882},
    'Lamb #1':{'OH':7614,'ST01':12422,'ST05':9312},
    'CMWW #1':{'OH':6827,'ST01':6796},
    'CMWW #2':{'OH':7205,'ST01':5883,'ST02':5539}
}
res = {'Well':[],'OH':[],'ST01':[],'ST02':[],'ST03':[],'ST04':[],'ST05':[]}

for well in os.listdir(path=path):
    print(well)
    res['Well'].append(well)
    files = os.listdir(path=f'{path}\\{well}')
    sts = ['Well']
    for file in files:
        st = file[:-5];sts.append(st)
        df = pd.read_excel(f'{path}\\{well}\\{file}')
        found = False
        if well in stpoints.keys():
            if st in stpoints[well].keys():
                found = True
                stp = stpoints[well][st]
                mask = df['MD'] < stp
                df = df[~mask]
        if not found: res[st].append('no stp');continue
        df = df.sort_values(['MD'], ascending = [True])
        df['prevmd'] = df['MD'].shift(1); df.loc[0,'prevmd'] = 0
        df['dl'] = df['DLS']/100*(df['MD'] - df['prevmd'])
        ss = df['dl'].sum()
        res[st].append(ss)

    opts = res.keys()
    add = [i for i in opts if i not in sts]
    for a in add: res[a].append(None)
    sts = ['Well']
print(pd.DataFrame(res))
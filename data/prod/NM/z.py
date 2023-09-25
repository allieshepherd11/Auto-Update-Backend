import pandas as pd
pd.set_option('display.max_columns',None)
d = pd.read_json('data\prod\\NM\\allocations.json').to_dict()
print(d)

res = {'Date':[],'Id':[],'Well Name':[],'Well Nums': [],'Test Well':[],
       'Test Oil':[],'Test Gas':[], 'Test Water':[]}
for idd in d.keys():
    if len(d[idd]['wells']) == 2:
        res['Id'].append(idd)
        res['Date'].append('2023-08-13')
        res['Well Name'].append(d[idd]['name'])
        res['Well Nums'].append(d[idd]['wells'])
        for col in ['Test Well',
       'Test Oil','Test Gas', 'Test Water'
       ]: res[col].append(None)

rows = {'Date':[],'Id':[],'Well Name':[],'Well Nums': [],'Test Well':[],
       'Test Oil':[],'Test Gas':[], 'Test Water':[]}
pad19 = d[11464]['tests']['2023-08']
pad15 = d[11458]['tests']['2023-08']
dates = {0:{
    '1':['08','09','10'],'4':['01','02','03','04','05','06','14','15','16'],'5':['07','11','12','13']
       },1:{
           '1':['07','08','09','10','11','12','13'],'2':['14','15','16'],'3':['01','02','03','04','05','06']
       }
}
for idx,pad in enumerate([pad19,pad15]):
       print(f'id {idx}')
       name = 'Paddy 19 State' if idx == 0 else 'Paddy 15 State'
       idd = 11464 if idx == 0 else 11458
       wns = [1,4,5] if idx == 0 else [1,2,3]
       for wn in pad:
              cnt = 0
              for o,g,w in zip(pad[wn]['oil'],pad[wn]['gas'],pad[wn]['water']):
                     rows['Date'].append(f'2023-08-{dates[idx][wn][cnt]}'); rows['Well Nums'].append(wns)
                     rows['Id'].append(idd); rows['Well Name'].append(name)
                     rows['Test Well'].append(wn)
                     rows['Test Oil'].append(o)
                     rows['Test Gas'].append(g)
                     rows['Test Water'].append(w)
                     cnt+=1
print(pd.DataFrame(rows))
print(pad19)

exit()

df = pd.DataFrame(res)
print(df)


import os 

fields = ['ST','ET','WB','NM','WT','GC']
path = 'data/prod'
for field in fields:
    path = f'data/prod/{field}'
    files = os.listdir(path=path)
    for file in files:
        if 'pdf' in file: os.remove(f'{path}/{file}');print(f'rm {file}')
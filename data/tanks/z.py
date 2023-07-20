import pandas as pd

df = pd.read_json('db\\tanks\\runTickets.json').fillna('del')

print(df)
d = df.to_dict(orient='records')
print(d)
delete = []
for i in d:
    for key,val in i.items():
        if val == "del":
            delete.append(key)
for dict_ in d:
    for key in delete:
        if key in dict_:
            del dict_[key]
print(d)
df = pd.DataFrame(d)
print(df)
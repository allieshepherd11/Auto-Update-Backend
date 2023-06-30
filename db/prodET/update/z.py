import pandas as pd
 

df = pd.read_json('db\\prodET\\update\\cumProd.json')
df_forms = pd.read_json('db\\prodET\\formations.json')
print(df)
print(df_forms)
res = df.merge(df_forms,on=0)

res.to_json('db\\prodET\\update\\cumlProd.json',orient='values',date_format='iso')


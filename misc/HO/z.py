import pandas as pd
import re

dfg = pd.read_excel('./misc/HO/hogrades.xlsx')
df = pd.read_excel('./misc/HO/holist.xlsx')

print(df)
dfg['Well'] = dfg['Well'].str.replace('#','')
dfg['Well'] = dfg['Well'].apply(lambda x: re.sub('r\d','',x))
print(dfg)

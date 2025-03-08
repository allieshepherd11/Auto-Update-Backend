import pandas as pd


df_st = pd.read_csv('data/prod/ST/data.csv')
df_et = pd.read_csv('data/prod/ET/data.csv')
df = pd.concat([df_st,df_et])
df_orbis = pd.read_excel("C:/Users/plaisancem/Downloads/orbis_wells.xlsx")
print(df_orbis)
orbis_wells = [w.lower().replace(' ','').replace('#','') for w in df_orbis['Well Name'].tolist()]

print(orbis_wells)
add = ['beeler #16 RE','benge unit #1h','bruce weaver #1 RE','bruce weaver #2 re','cmww #1','cmww #2','coffman #1h','cr #939','drinakrd #1','dial #1 st','dixondale #1','fatheree #1','herbich #2h','hayes #1','hayes #2','jic #1','jicbuda #1','kleimann #3 re','marrs #1','mdb #1','mt unit #1','sansom #1']
for i in add: orbis_wells.append(i.lower().replace(' ','').replace('#',''))
namemap = {w.lower().replace(' ','').replace('#',''):w for w in sorted(set(df['Well Name'].tolist()))}
df['Well Name'] = df['Well Name'].str.lower()
df['Well Name'] = df['Well Name'].str.replace(' ','')
df['Well Name'] = df['Well Name'].str.replace('#','')

df_orbis_prod = df.loc[df['Well Name'].isin(orbis_wells)]
df_orbis_prod['Well Name'] = df_orbis_prod['Well Name'].apply(lambda x: namemap[x] if x in namemap.keys() else x)
df_orbis_prod['Well Name'] = df_orbis_prod['Well Name'].str.title()
df_orbis_prod = df_orbis_prod[["Well Name","Date","Oil (BBLS)","Gas (MCF)","Water (BBLS)"]]
df_orbis_prod.to_csv('Orbis Production 2025-02-07.csv',index=False)
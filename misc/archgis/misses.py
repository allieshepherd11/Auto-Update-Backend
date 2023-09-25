import pandas as pd



wells = sorted(set(pd.read_csv('data\prod\ST\moData.csv')['Well Name'].tolist()))
wells = [w.lower() for w in wells]
apiwells = sorted(set(pd.read_csv('misc/archgis/apinumsst.csv')['Well Name'].tolist()))
apiwells = [w.lower() for w in apiwells]

for well in wells: 
    if well not in apiwells:print(well.upper())
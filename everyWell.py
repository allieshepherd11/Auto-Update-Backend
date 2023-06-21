import pandas as pd
import json

df = pd.read_csv('monthlyDataST.csv')
wells = df["Well Name"].to_list()
wells = set(wells)
wells = list(wells)

# Open the file in write mode
with open('everyWell.json', 'w') as json_file:
    # Use the json.dump() function to write the list to the file
    json.dump(wells, json_file)
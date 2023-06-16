import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from lxml import html
import requests
from collections import OrderedDict
import json

def main():
    declineCurve()

def declineCurve():
    data = pd.read_csv('monthlyDataST.csv')
    df = data[data['Well Name'] == "Carolpick #1"]
    df_filtered = df.drop(df.index[-1])
    # exclude first month data & current month data

    df_filtered.to_csv("test.csv", index=False)
    


    
main()

import pandas as pd
import datetime
#pd.set_option('display.max_rows', None)  
#pd.set_option('display.max_columns', None)  

def pl(file,keep):
    df = pd.read_excel(file)
    print(df.columns)
    yr = file[-10:][0:2]
    print(yr)
    stmts = []
    well_col = ""
    for col in df.columns:
        if isinstance(col,datetime.datetime):
            if yr in col.strftime("%Y-%m-%d"):
                stmts.append(col)
        else:
            if "Well" in col and "#" not in col:
                stmts.append(col)
                well_col = col
    df = df[stmts]
    
    print(df)
    dictionary = {}
    #mo = ["Jan 23", "Feb 23", "Mar 23", "Apr 23", "May 23"]
    for index, row in df.iterrows():
        well = row[well_col]
        dictionary[well] = {}
        for col in df.columns:
            if isinstance(col,datetime.datetime):
                key = col.strftime("%b %y")
                if len(keep) > 0:
                    if key in keep:
                        if isinstance(key,str):
                            print(f'string :: {key}')
                        dictionary[well][key] = round(row[col],2)
                else:
                    try:
                        dictionary[well][key] = round(row[col],2)
                    except TypeError as err:
                        dictionary[well][key] = 0.00

    return dictionary
    

def combine_dicts(dict1, dict2):
    res = dict1.copy()
    
    for key in dict2.keys():
        if key in res:
            for mo,val in dict2[key].items():
                
                dict1[key][mo] = val
        else:
            res[key] = dict2[key]
    
    return res

def main():
    pl16 = pl('./backups/econ/2016p&L.xlsx',[])
    pl17 = pl('./backups/econ/2017p&L.xlsx',[])
    pl18 = pl('./backups/econ/2018p&L.xlsx',[])
    pl19 = pl('./backups/econ/2019p&L.xlsx',[])
    pl20 = pl('./backups/econ/2020p&L.xlsx',[])
    pl21 = pl('./backups/econ/2021p&L.xlsx',[])
    pl22 = pl('./backups/econ/2022p&l.xlsx',[])
    pl23 = pl('db\econ\\2023_P&L.xlsx',["Jan 23", "Feb 23", "Mar 23", "Apr 23"])
    c1 = combine_dicts(pl16, pl17)
    print(f'c1 : {c1}')
    c2 = combine_dicts(c1, pl18)
    print(f'c2 : {c2}')
    exit()
    c3 = combine_dicts(c2, pl19)
    c4 = combine_dicts(c3, pl20)
    c5 = combine_dicts(c4, pl21)
    c6 = combine_dicts(c5, pl22)
    c7 = combine_dicts(c6, pl23)

    print('\n',c7)
    resdf = pd.DataFrame([c7])
    resdf.to_json('16_23pl.json',orient="records")
main()
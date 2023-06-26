import pandas as pd
import datetime

def pl(file,keep):
    df = pd.read_excel(file)
    yr = file[-10:][0:2]
    stmts = []
    well_col = ""
    well_map = {}
    for col in df.columns:
        if isinstance(col,datetime.datetime):
            if yr in col.strftime("%Y-%m-%d"):
                stmts.append(col)
        else:
            if "Well" in col and "#" in col:
                stmts.append(col)
                well_col = col
                well_map[col] = ""
    for col in df.columns:
        if not isinstance(col,datetime.datetime):
            if "Well" in col and "#" not in col:
                well_map[well_col] = col     
    print(f'well map : {well_map}')
    df = df[stmts]
    
    df = df.rename(columns={well_col : "Well Number"})

    df = df[df["Well Number"] != float('nan')]
    df["Well Number"] = df["Well Number"].astype(str)
    for col in df.columns:
        if isinstance(col,datetime.datetime):
            df.rename(columns={col: col.strftime("%b %y")}, inplace=True)
    return df,well_map
def main():
    pd.set_option('display.max_columns',None)
    pl16,well_map16 = pl('./backups/econ/2016p&L.xlsx',[])
    pl17,well_map17 = pl('./backups/econ/2017p&L.xlsx',[])
    pl18,well_map18 = pl('./backups/econ/2018p&L.xlsx',[])
    pl19,well_map19 = pl('./backups/econ/2019p&L.xlsx',[])
    pl20,well_map20 = pl('./backups/econ/2020p&L.xlsx',[])
    pl21,well_map21 = pl('./backups/econ/2021p&L.xlsx',[])
    pl22,well_map22 = pl('./backups/econ/2022p&l.xlsx',[])
    pl23,well_map23 = pl('db\econ\\2023p&l.xlsx',["Jan 23", "Feb 23", "Mar 23", "Apr 23"])

    combined_df = pl16.merge(pl17, on='Well Number', how='outer').merge(pl18, on='Well Number', how='outer') \
        .merge(pl19, on='Well Number', how='outer').merge(pl20, on='Well Number', how='outer').merge(pl21, on='Well Number', how='outer') \
        .merge(pl22, on='Well Number', how='outer').merge(pl23, on='Well Number', how='outer')
    combined_df = combined_df.drop(['May 23','Jun 23','Jul 23','Aug 23','Sep 23','Oct 23','Nov 23','Dec 23'],axis=1)
    #print(f': {combined_df}')
    
    resdf = pd.DataFrame(combined_df)
    resdf.to_json('a.json',orient="records")

    well_map = {}
    for dictionary in [well_map16, well_map17, well_map18, well_map19, well_map20,well_map21, well_map22, well_map23]:
        temp_dict = {k: v for k, v in dictionary.items() if k not in well_map}
        well_map.update(temp_dict)

    print(well_map)
main()
import pandas as pd

def handle(dfNymex,dfDetail,name):
    dfNymex['Well'] = dfNymex['Well'].str.replace('#', '')
    dfNymex['Well'] = dfNymex['Well'].str.replace('Unit', '')
    dfNymex['Well'] = dfNymex['Well'].str.replace('UNIT', '')
    dfNymex['Well'] = dfNymex['Well'].str.replace("'", '')
    dfNymex['Well'] = dfNymex['Well'].str.replace('.', '')
    dfNymex['Well'] = dfNymex['Well'].str.lower()

    dfDetail['Well'] = dfDetail['Well'].str.replace('#', '')
    dfDetail['Well'] = dfDetail['Well'].str.replace('Unit', '')
    dfDetail['Well'] = dfDetail['Well'].str.replace('UNIT', '')
    dfDetail['Well'] = dfDetail['Well'].str.replace("'", '')
    dfDetail['Well'] = dfDetail['Well'].str.replace('.', '')
    dfDetail['Well'] = dfDetail['Well'].str.lower()

    dfDetail['Nymex PV'] = None


    for index, row in dfNymex.iterrows():
        matching_row_index = dfDetail.index[dfDetail['Well'] == row['Well']].tolist()
        
        if matching_row_index:
            dfDetail.at[matching_row_index[0], 'Nymex PV'] = row['Curr PV']
    print(dfDetail)

    dfDetail.to_csv(f'misc/ken/{name}.csv')


detailMainExc = pd.ExcelFile('misc/ken/Detail Main.xlsx')
nymexExc = pd.ExcelFile('misc/ken/nymex.xlsx')

dfDetail = pd.read_excel(detailMainExc,'KCN Sep Prop')
dfNymex = pd.read_excel(nymexExc,'01-03-2024 Field List NYMEX')

for sn in ['CML Detail','KCN Sep Prop','JACA','Trusts','Travis','Phil']:
    print(sn)
    handle(dfNymex=dfNymex,
           dfDetail=pd.read_excel(detailMainExc,sn),name=sn)

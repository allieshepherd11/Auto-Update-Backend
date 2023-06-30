import pandas as pd
from scipy.optimize import minimize

def solver(df):#one column with oil
    def arps(t,x0):
        b = x0[2]
        di = x0[1]
        qi = x0[0]        
        return qi/((1+(b*t*di)**(1/b)))

    def sum_err(x0):
        sqerr = 0
        for idx,row in df.iterrows():
            #t = idx
            sqerr += (row[0] - arps(idx,x0))**2
        return sqerr

    x0 = [20000,.6,.6]#init guesses : qi,di,b
    bounds = [(0,None),(0,None),(0,1)]

    res = minimize(sum_err,x0,method='Nelder-Mead',bounds=bounds)

    return {"params":res.x , "sq err": res.fun}

def forecast(di,qi,b,t):#forecast reserves from current time
    limit = 140
    qcurr = qi/((1+(b*t*di)**(1/b)))
    print("qcurr:", qcurr)
    dcurr = di/(1 + b*di*t)
    print("dcurr:", dcurr)
    np = (qcurr**b)*(qcurr**(1-b) - limit**(1-b))/((1-b)*dcurr)

    n = (qcurr - qi)/di
    print(f'n : {n}')
    return np

def format():
    #df = pd.read_json("db\prod\\allProductionData.json")
    df = pd.read_csv("db\prod\monthlyDataST.csv")
    df = df.drop(columns=["Gas (MCF)", "Water (BBLS)", "TP","CP"])

    df_groups = df.groupby("Well Name")
    groups = list(df_groups.groups.keys())

    cannan = df_groups.get_group("Cannan #1")
    cannan.to_csv('db/prod/declineCannan.csv',index=False)

    print(df)

    return

def main():
    df = pd.read_csv('db/prod/decline.csv')#montly prod 
   
    res = solver(df)#"params": [qi,di,b]
    print(res["params"])
    params = res["params"]
    np = forecast(params[1],params[0],params[2],len(df)-1)
    print(np)

main()
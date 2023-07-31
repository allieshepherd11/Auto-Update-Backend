import pandas as pd

def gc():
    df = pd.read_csv('data\prod\GC\data.csv')
    print(df[:20],'\n')
    print(df[-20:])


    df.loc[df['Well Name'] == 'LOTTIE #1','Well Name'] = 'Lottie #1'
    df.loc[df['Well Name'] == "DYER 'D' #5",'Well Name'] = "Dyer 'D' #5"
    df.loc[df['Well Name'] == 'MUELLER #1','Well Name'] = "Mueller #1"
    df.loc[df['Well Name'] == 'PRATKA #1','Well Name'] = 'Pratka #1'
    print(df[:20],'\n')
    print(df[-20:])

    mask = df['Well Name'] == 'Dyer 2 Sales Tap'
    df = df[~mask]
    mask = df['Well Name'] == 'JM Moore 92 SWD'
    df = df[~mask]
    mask = df['Well Name'] == 'Moore CL 10 SWD'
    df = df[~mask]
    print(df)
    df.to_csv('data\prod\GC\data.csv',index=False)

def nm():
    df = pd.read_csv('data\prod\\NM\data.csv')
    mask = df['Well Name'] == 'Mcwf #1'
    mask = df['Well Name'] == 'Cooper 24 Federal #2 Swd'
    df = df[~mask]

    print(df)

    df.to_csv('data\prod\\NM\data.csv',index=False)

def wt():
    df = pd.read_csv('data\prod\WT\data.csv')

    df.loc[df['Well Name'] == 'BROTHERS HORIZON UNIT','Well Name'] = 'Brothers Horizon Unit 1'
    df.loc[df['Well Name'] == 'BROTHERS HORIZON','Well Name'] = 'Brothers Horizon'
    df.loc[df['Well Name'] == 'MULESHOE RANCH #1','Well Name'] = 'Muleshoe Ranch #1'

    df.loc[df['Well Name'] == 'BECK UNIT #1','Well Name'] = 'Beck Unit #1'

    df.loc[df['Well Name'] == "KOONSMAN '677'",'Well Name'] = 'Koonsman 677'

    df.loc[df['Well Name'] == "EVERETT UNIT #1",'Well Name'] = 'Everett Unit #1'

    df.loc[df['Well Name'] == "BRUMLEY LEASE",'Well Name'] = 'Brumley'

    df.loc[df['Well Name'] == "EDWARDS '12' #1",'Well Name'] = 'Edwards 12 #1'
    df.loc[df['Well Name'] == "BLAIR-TXL  #3",'Well Name'] = 'Blair TXL 7 #3'
    df.loc[df['Well Name'] == "BLAIR-TXL  #1",'Well Name'] = 'Blair TXL 7 #1'

    df.loc[df['Well Name'] == "SLAUGHTER B",'Well Name'] = 'Slaughter B'
    df.loc[df['Well Name'] == "LLB '15' #1",'Well Name'] = 'LLB 15 #1'

    df.loc[df['Well Name'] == "BULLARD #5-#9",'Well Name'] = 'Bullard'
    df.loc[df['Well Name'] == 'KIM','Well Name'] = 'Kim'

    df.loc[df['Well Name'] == 'Davis Lease','Well Name'] = 'Davis 3'#change iwell alias
    df.loc[df['Well Name'] == 'DAVIS 3','Well Name'] = 'Davis 3'

    df.loc[df['Well Name'] == 'North JUMF','Well Name'] = 'North JUWF'
    df.loc[df['Well Name'] == 'South JUMF','Well Name'] = 'South JUWF'

    df.to_csv('data\prod\WT\data.csv',index=False)
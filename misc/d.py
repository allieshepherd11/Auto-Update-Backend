import pandas as pd

df = pd.read_csv("data\prod\ST\moData.csv")
df = df[df['Well Name'] == 'J Beeler #1'].reset_index(drop=True)
df = df.drop([col for col in df.columns if col not in ['Oil (BBLS)','Gas (MCF)','Date']],axis=1).reset_index(drop=True)
print(df)
df.to_csv('jbeeler.csv',index=False)
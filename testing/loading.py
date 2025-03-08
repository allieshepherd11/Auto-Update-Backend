import pandas as pd


df = pd.read_csv('testing\TAM Loading Jan 25.csv')

df['Date'] = pd.to_datetime(df['Date'])

# Filter out rows where 'Value' is None/NaN
df = df[df['Beam Loading (%)'].notna()]

# Get the most recent row for each name
df = df.loc[df.groupby('Well Name')['Date'].idxmax()]

print(df)

print(df)
df.to_excel('TAM Loading Recent.xlsx',index=False)
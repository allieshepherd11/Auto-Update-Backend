import pandas as pd


df = pd.read_csv(r"C:\Users\plaisancem\Documents\union ac.csv")

df = df.sort_values(['WellName','ProducingMonth'], ascending = [True , False]).reset_index(drop=True)



def has_substantial_uplift(group):
    group = group.sort_values('ProducingMonth')
    for idx, row in group.iterrows():
        if idx < 7:continue
        if row['LiquidsProd_BBL'] < 500:
            later = group[group['ProducingMonth'] > row['ProducingMonth']]
            if (later['LiquidsProd_BBL'] > 1200).any():
                return True
    return False

wells_with_uplift = df.groupby('WellName').filter(has_substantial_uplift)

uplift_wells = wells_with_uplift['WellName'].unique()
uplift_wells_api = wells_with_uplift['API_UWI'].unique()
for i in uplift_wells_api:print(i)

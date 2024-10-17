import pandas as pd

# List of months and wells
months = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
]
yr = 20

# Read the original CSV
df = pd.read_csv('wells.csv')

# Extract the list of wells
wells = df['Well'].tolist()

# Create a new DataFrame structure
data = {'Well': [], 'month': []}
for m in months:
    for well in wells:
        data['Well'].append(well)
        # Prefix with an apostrophe to prevent Excel from converting to date
        data['month'].append(f"'{m} {yr}")

# Create DataFrame
df = pd.DataFrame(data)

# Write to CSV
df.to_csv('wells20.csv', index=False)

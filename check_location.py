import pandas as pd

phone = '201030454023'

# Check retailers_profiles
retailers = pd.read_csv('retailers_profiles.csv', sep='\t', encoding='utf-8')
matches = retailers[retailers['phone'].astype(str) == phone]
print(f'Rows with phone {phone} in retailers_profiles: {len(matches)}')
if len(matches) > 0:
    print(matches[['retailer_name', 'phone', 'area', 'city']].head())

# Check overall.csv
overall = pd.read_csv('overall.csv', sep='\t', encoding='utf-8')
matches2 = overall[overall['phone'].astype(str) == phone]
print(f'\nRows with phone {phone} in overall.csv: {len(matches2)}')
if len(matches2) > 0:
    print(f'Unique names: {matches2["name"].unique()[:10]}')
    print(matches2[['name', 'phone']].head(10))


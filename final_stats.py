import pandas as pd

df = pd.read_csv('data_cleaned_enriched.csv', sep='\t', encoding='utf-8')

print('Final Statistics:')
print(f'Total rows: {len(df):,}')
print(f'Location rows: {(df["name"] == "Location").sum()}')
print(f'Unique customers: {df["name"].nunique():,}')
print(f'Unique phones: {df["phone"].nunique():,}')
print(f'Unique products: {df["product"].nunique():,}')
print(f'Unique brands: {df["brand"].nunique():,}')
print(f'Total GMV: {(df["amount"] * df["price_gross"]).sum():,.2f}')


import pandas as pd
import re
from collections import defaultdict

# Read the CSV file
df = pd.read_csv('data.csv', sep='\t', encoding='utf-8')

# City mapping - standardize city names
CITY_MAPPING = {
    'Cairo': 'Cairo Governorate',
    'Cairo Governorate': 'Cairo Governorate',
    'Giza': 'Giza Governorate',
    'Giza Governorate': 'Giza Governorate',
    'Al Giza': 'Giza Governorate',
    'الجيزه': 'Giza Governorate',
    'الجيزة': 'Giza Governorate',
    'القاهرة': 'Cairo Governorate',
    'الإسكندرية': 'Alexandria Governorate',
    'Alexandria': 'Alexandria Governorate',
    'Alexandria Governorate': 'Alexandria Governorate',
    'Al-Qalyubia': 'Al-Qalyubia Governorate',
    'Al-Qalyubia Governorate': 'Al-Qalyubia Governorate',
    'القليوبية': 'Al-Qalyubia Governorate',
    'Al-Sharqia': 'Al-Sharqia Governorate',
    'Al-Sharqia Governorate': 'Al-Sharqia Governorate',
    'الشرقية': 'Al-Sharqia Governorate',
    'Suez': 'Suez Governorate',
    'Suez Governorate': 'Suez Governorate',
    'السويس': 'Suez Governorate',
    'Ismailia': 'Ismailia Governorate',
    'Ismailia Governorate': 'Ismailia Governorate',
    'Menofia': 'Menofia Governorate',
    'Menofia Governorate': 'Menofia Governorate',
    'المنوفية': 'Menofia Governorate',
    'Gharbia': 'Gharbia Governorate',
    'Gharbia Governorate': 'Gharbia Governorate',
    'الغربية': 'Gharbia Governorate',
    'Dakahlia': 'Dakahlia Governorate',
    'Dakahlia Governorate': 'Dakahlia Governorate',
    'الدقهلية': 'Dakahlia Governorate',
    'Beheira': 'Beheira Governorate',
    'Beheira Governorate': 'Beheira Governorate',
    'البحيرة': 'Beheira Governorate',
    'Qena': 'Qena Governorate',
    'Qena Governorate': 'Qena Governorate',
    'قنا': 'Qena Governorate',
    'Faiyum': 'Faiyum Governorate',
    'Faiyum Governorate': 'Faiyum Governorate',
    'الفيوم': 'Faiyum Governorate',
    'Beni Suef': 'Beni Suef Governorate',
    'Beni Suef Governorate': 'Beni Suef Governorate',
    'بني سويف': 'Beni Suef Governorate',
}

def extract_city_from_address(address):
    """Extract city from address if missing"""
    if pd.isna(address) or address.strip() == '':
        return None
    
    address = str(address)
    
    # Look for city patterns in the address
    for city_pattern, standardized in CITY_MAPPING.items():
        if city_pattern.lower() in address.lower():
            return standardized
    
    return None

def extract_area_from_address(address):
    """Extract area from address"""
    if pd.isna(address) or address.strip() == '':
        return None
    
    address = str(address)
    
    # Split by comma and filter out governorate/city parts and postal codes
    parts = [p.strip() for p in address.split(',') if p.strip()]
    
    if len(parts) > 1:
        # Try to find area (usually before the governorate)
        for part in reversed(parts):
            # Skip if it's a city/governorate
            is_city = any(city.lower() in part.lower() for city in CITY_MAPPING.keys())
            # Skip if it's mostly numbers (postal code)
            is_postal = bool(re.match(r'^\d+', part))
            
            if not is_city and not is_postal:
                return part
    
    return None

# Clean the data
print("Cleaning data...")

# If area and city columns exist, try to fill missing values from address
if 'area' in df.columns and 'address' in df.columns:
    # Fill missing areas
    missing_area_mask = df['area'].isna() | (df['area'].str.strip() == '')
    df.loc[missing_area_mask, 'area'] = df.loc[missing_area_mask, 'address'].apply(extract_area_from_address)
    
    # Fill missing areas with 'غير محدد' if still empty
    df['area'] = df['area'].fillna('غير محدد')
    df.loc[df['area'].str.strip() == '', 'area'] = 'غير محدد'

if 'city' in df.columns and 'address' in df.columns:
    # Fill missing cities
    missing_city_mask = df['city'].isna() | (df['city'].str.strip() == '')
    df.loc[missing_city_mask, 'city'] = df.loc[missing_city_mask, 'address'].apply(extract_city_from_address)
    
    # Standardize city names
    df['city'] = df['city'].apply(lambda x: CITY_MAPPING.get(str(x).strip(), x) if pd.notna(x) else 'غير محدد')
    
    # Fill remaining empty cities
    df['city'] = df['city'].fillna('غير محدد')
    df.loc[df['city'].str.strip() == '', 'city'] = 'غير محدد'

# Remove duplicate postal codes from city names (e.g., "Cairo Governorate 11765" -> "Cairo Governorate")
if 'city' in df.columns:
    df['city'] = df['city'].apply(lambda x: re.sub(r'\s+\d+$', '', str(x)) if pd.notna(x) else x)

# Print statistics
print(f"\n=== Data Cleaning Summary ===")
print(f"Total records: {len(df)}")

if 'city' in df.columns:
    print(f"\nUnique cities: {df['city'].nunique()}")
    print("\nTop cities:")
    print(df['city'].value_counts().head(10))

if 'area' in df.columns:
    print(f"\nUnique areas: {df['area'].nunique()}")
    print("\nTop areas:")
    print(df['area'].value_counts().head(10))

if 'name' in df.columns:
    print(f"\nUnique customers: {df['name'].nunique()}")

# Save cleaned data
cleaned_file = 'data_cleaned.csv'
df.to_csv(cleaned_file, index=False, encoding='utf-8', sep='\t')
print(f"\nCleaned data saved to: {cleaned_file}")

# Create summary for analysis
print("\n=== Missing Data Analysis ===")
missing_summary = df.isnull().sum()
print(missing_summary[missing_summary > 0])

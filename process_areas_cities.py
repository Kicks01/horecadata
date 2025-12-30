#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Process customers data to extract and consolidate cities and areas
"""
import pandas as pd
import json
from collections import defaultdict

# Read the cleaned data
df = pd.read_csv('data_cleaned.csv')

# Create city and area mapping for consolidation
CITY_MAPPING = {
    'محافظة القاهرة': 'Cairo Governorate',
    'محافظة الجيزة': 'Giza Governorate', 
    'محافظة الإسكندرية': 'Alexandria Governorate',
    'محافظة القليوبية': 'Al-Qalyubia Governorate',
    'محافظة الدقهلية': 'Dakahlia Governorate',
    'محافظة الشرقية': 'Al-Sharqia Governorate',
    'محافظة الغربية': 'Gharbia Governorate',
    'محافظة المنوفية': 'Menofia Governorate',
    'محافظة الفيوم': 'Faiyum Governorate',
    'محافظة بنى سويف': 'Beni Suef Governorate',
    'محافظة المنيا': 'Minya Governorate',
    'محافظة أسيوط': 'Assiut Governorate',
    'محافظة سوهاج': 'Sohag Governorate',
    'محافظة قنا': 'Qena Governorate',
    'محافظة الأقصر': 'Luxor Governorate',
    'محافظة أسوان': 'Aswan Governorate',
    'محافظة مطروح': 'Matrouh Governorate',
    'محافظة البحر الأحمر': 'Red Sea Governorate',
    'محافظة السويس': 'Suez Governorate',
    'محافظة الإسماعيلية': 'Ismailia Governorate',
    'محافظة بورسعيد': 'Port Said Governorate',
}

AREA_MAPPING = {
    'مدينة نصر‎‎‎‎': 'Cairo Governorate - Nasr City',
    'مدينة نصر': 'Cairo Governorate - Nasr City',
    'Nasr City': 'Cairo Governorate - Nasr City',
    'El Golf': 'Cairo Governorate - Nasr City - Al Golf',
    'Al Golf': 'Cairo Governorate - Nasr City - Al Golf',
    'المعصرة': 'Cairo Governorate - Al Maasoura',
    'Al Maasoura': 'Cairo Governorate - Al Maasoura',
    'البساتين': 'Cairo Governorate - El Basatin',
    'El Basatin': 'Cairo Governorate - El Basatin',
    'الهرم': 'Giza Governorate - Al Haram',
    'Al Haram': 'Giza Governorate - Al Haram',
    'الدقي': 'Giza Governorate - Ad Doqi',
    'Ad Doqi': 'Giza Governorate - Ad Doqi',
    'Dokki': 'Giza Governorate - Dokki',
}

# Get unique cities and areas from data
cities = df['city'].dropna().unique()
areas = df['area'].dropna().unique()

print(f"Total unique cities: {len(cities)}")
print(f"Total unique areas: {len(areas)}")

# Filter out 'غير محدد' (undefined)
valid_cities = [c for c in cities if c and c != 'غير محدد']
valid_areas = [a for a in areas if a and a != 'غير محدد']

print(f"\nValid cities (without 'غير محدد'): {len(valid_cities)}")
print(f"Valid areas (without 'غير محدد'): {len(valid_areas)}")

# Group customers by city and area
customers_by_city = defaultdict(list)
customers_by_area = defaultdict(list)
customers_by_city_area = defaultdict(lambda: defaultdict(list))

for idx, row in df.iterrows():
    customer_name = row['name']
    if customer_name not in ['Location'] and pd.notna(customer_name):
        city = row['city'] if pd.notna(row['city']) and row['city'] != 'غير محدد' else None
        area = row['area'] if pd.notna(row['area']) and row['area'] != 'غير محدد' else None
        
        if city:
            customers_by_city[city].append(customer_name)
        if area:
            customers_by_area[area].append(customer_name)
        if city and area:
            customers_by_city_area[city][area].append(customer_name)

# Remove duplicates
for key in customers_by_city:
    customers_by_city[key] = list(set(customers_by_city[key]))
for key in customers_by_area:
    customers_by_area[key] = list(set(customers_by_area[key]))

print(f"\nCustomers by city: {len(customers_by_city)}")
print(f"Customers by area: {len(customers_by_area)}")

# Save mapping data
with open('city_area_mapping.json', 'w', encoding='utf-8') as f:
    json.dump({
        'city_mapping': CITY_MAPPING,
        'area_mapping': AREA_MAPPING,
        'cities': {city: len(customers) for city, customers in customers_by_city.items()},
        'areas': {area: len(customers) for area, customers in customers_by_area.items()},
    }, f, ensure_ascii=False, indent=2)

print("\n✅ Mapping file created: city_area_mapping.json")

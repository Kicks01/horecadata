"""
Enhanced Data Enrichment Script
Uses all reference files intelligently to fill missing data
"""

import pandas as pd
import json
import re
import sys
from collections import defaultdict

# Ensure UTF-8 output on Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

def normalize_phone(phone):
    """Normalize phone numbers for matching"""
    if pd.isna(phone):
        return None
    phone = str(phone).strip()
    phone = re.sub(r'\D', '', phone)
    return phone

print("=" * 80)
print("ENHANCED DATA ENRICHMENT SCRIPT")
print("=" * 80)
sys.stdout.flush()

# Load data files
print("\n[1/7] Loading data files...")
sys.stdout.flush()

try:
    data_cleaned = pd.read_csv('data_cleaned.csv', sep='\t', low_memory=False, encoding='utf-8')
    print(f"   [OK] Loaded data_cleaned.csv: {len(data_cleaned):,} rows")
except Exception as e:
    print(f"   [ERROR] Error loading data_cleaned.csv: {e}")
    sys.exit(1)

try:
    retailers_profiles = pd.read_csv('retailers_profiles.csv', sep='\t', low_memory=False, encoding='utf-8')
    if 'Unnamed: 3' in retailers_profiles.columns:
        retailers_profiles = retailers_profiles.drop(columns=['Unnamed: 3'])
    print(f"   [OK] Loaded retailers_profiles.csv: {len(retailers_profiles):,} rows")
except Exception as e:
    print(f"   [ERROR] Error loading retailers_profiles.csv: {e}")
    retailers_profiles = pd.DataFrame()

try:
    base_products = pd.read_csv('base-products-2025-11-27.csv', low_memory=False, encoding='utf-8')
    print(f"   [OK] Loaded base-products-2025-11-27.csv: {len(base_products):,} rows")
except Exception as e:
    print(f"   [ERROR] Error loading base-products-2025-11-27.csv: {e}")
    base_products = pd.DataFrame()

try:
    overall = pd.read_csv('overall.csv', sep='\t', low_memory=False, encoding='utf-8')
    print(f"   [OK] Loaded overall.csv: {len(overall):,} rows")
except Exception as e:
    print(f"   [ERROR] Error loading overall.csv: {e}")
    overall = pd.DataFrame()

sys.stdout.flush()

# Build phone-to-retailer mapping from retailers_profiles
print("\n[2/7] Building retailer mapping from retailers_profiles...")
sys.stdout.flush()

phone_to_retailer = {}
if not retailers_profiles.empty:
    retailers_profiles['phone_norm'] = retailers_profiles['phone'].apply(normalize_phone)
    
    for phone_norm, group in retailers_profiles.groupby('phone_norm'):
        if pd.notna(phone_norm):
            group = group.copy()
            group['score'] = (
                group['retailer_name'].notna().astype(int) * 2 +
                group['area'].notna().astype(int) +
                group['city'].notna().astype(int) +
                group['distribution_route'].notna().astype(int) +
                group['retailer_type'].notna().astype(int)
            )
            best = group.loc[group['score'].idxmax()]
            phone_to_retailer[phone_norm] = {
                'retailer_name': str(best.get('retailer_name', '')).strip() if pd.notna(best.get('retailer_name')) else '',
                'retailer_type': str(best.get('retailer_type', '')).strip() if pd.notna(best.get('retailer_type')) else '',
                'area': str(best.get('area', '')).strip() if pd.notna(best.get('area')) else '',
                'city': str(best.get('city', '')).strip() if pd.notna(best.get('city')) else '',
                'route': str(best.get('distribution_route', '')).strip() if pd.notna(best.get('distribution_route')) else ''
            }

print(f"   [OK] Cached {len(phone_to_retailer):,} retailer mappings from retailers_profiles")
sys.stdout.flush()

# Build phone-to-retailer mapping from overall.csv (as fallback/enhancement)
print("\n[3/7] Building retailer mapping from overall.csv...")
sys.stdout.flush()

phone_to_retailer_overall = {}
if not overall.empty:
    overall['phone_norm'] = overall['phone'].apply(normalize_phone)
    
    for phone_norm, group in overall.groupby('phone_norm'):
        if pd.notna(phone_norm):
            # Get most common name (not "Location")
            names = group[group['name'].notna() & (group['name'] != 'Location')]['name']
            if len(names) > 0:
                # Get most frequent name
                name_counts = names.value_counts()
                most_common_name = name_counts.index[0]
                
                # Get area and city if available (overall.csv may not have these columns)
                area = ''
                city = ''
                if 'area' in group.columns:
                    areas = group[group['area'].notna() & (group['area'] != '')]['area']
                    area = areas.value_counts().index[0] if len(areas) > 0 else ''
                if 'city' in group.columns:
                    cities = group[group['city'].notna() & (group['city'] != '')]['city']
                    city = cities.value_counts().index[0] if len(cities) > 0 else ''
                
                # Infer type from name
                retailer_type = ''
                name_lower = most_common_name.lower()
                if any(word in name_lower for word in ['مطعم', 'restaurant']):
                    retailer_type = 'Restaurant'
                elif any(word in name_lower for word in ['كافيه', 'cafe', 'coffee']):
                    retailer_type = 'Cafe'
                elif any(word in name_lower for word in ['مخبز', 'bakery']):
                    retailer_type = 'Bakery'
                
                phone_to_retailer_overall[phone_norm] = {
                    'retailer_name': most_common_name,
                    'retailer_type': retailer_type,
                    'area': area,
                    'city': city,
                    'route': ''
                }

print(f"   [OK] Cached {len(phone_to_retailer_overall):,} retailer mappings from overall.csv")
sys.stdout.flush()

# Merge mappings (prioritize retailers_profiles, but use overall for missing data)
for phone_norm, info in phone_to_retailer_overall.items():
    if phone_norm not in phone_to_retailer:
        phone_to_retailer[phone_norm] = info
    else:
        # Enhance existing entry with data from overall
        if not phone_to_retailer[phone_norm]['retailer_name'] and info['retailer_name']:
            phone_to_retailer[phone_norm]['retailer_name'] = info['retailer_name']
        if not phone_to_retailer[phone_norm]['area'] and info['area']:
            phone_to_retailer[phone_norm]['area'] = info['area']
        if not phone_to_retailer[phone_norm]['city'] and info['city']:
            phone_to_retailer[phone_norm]['city'] = info['city']
        if not phone_to_retailer[phone_norm]['retailer_type'] and info['retailer_type']:
            phone_to_retailer[phone_norm]['retailer_type'] = info['retailer_type']

print(f"   [OK] Total unique retailer mappings: {len(phone_to_retailer):,}")
sys.stdout.flush()

# Build base_id-to-product mapping
print("\n[4/7] Building product mapping cache...")
sys.stdout.flush()

base_id_to_product = {}
if not base_products.empty:
    for _, row in base_products.iterrows():
        base_id = row.get('ID')
        if pd.notna(base_id):
            try:
                base_id_int = int(float(base_id))
                name = str(row.get('Name', '')).strip() if pd.notna(row.get('Name')) else ''
                
                # Extract brand from name
                brand = ''
                if name:
                    words = name.split()
                    if len(words) > 0:
                        if len(words) > 1 and len(words[0]) < 5:
                            brand = ' '.join(words[:2])
                        else:
                            brand = words[0]
                
                base_id_to_product[base_id_int] = {
                    'product_name': name,
                    'brand': brand,
                    'category': ''
                }
            except:
                pass

# Enhance with overall.csv
if not overall.empty:
    for _, row in overall.iterrows():
        base_id = row.get('base_id')
        if pd.notna(base_id):
            try:
                base_id_int = int(float(base_id))
                product = str(row.get('product', '')).strip() if pd.notna(row.get('product')) else ''
                brand = str(row.get('brand', '')).strip() if pd.notna(row.get('brand')) else ''
                category = str(row.get('category', '')).strip() if pd.notna(row.get('category')) else ''
                
                if base_id_int not in base_id_to_product:
                    base_id_to_product[base_id_int] = {'product_name': '', 'brand': '', 'category': ''}
                
                if product and (not base_id_to_product[base_id_int]['product_name'] or len(product) > len(base_id_to_product[base_id_int]['product_name'])):
                    base_id_to_product[base_id_int]['product_name'] = product
                if brand and not base_id_to_product[base_id_int]['brand']:
                    base_id_to_product[base_id_int]['brand'] = brand
                if category and not base_id_to_product[base_id_int]['category']:
                    base_id_to_product[base_id_int]['category'] = category
            except:
                pass

print(f"   [OK] Cached {len(base_id_to_product):,} product mappings")
sys.stdout.flush()

# Enrich data
print("\n[5/7] Enriching data...")
sys.stdout.flush()

data_enriched = data_cleaned.copy()
improvements = {
    'retailer_name_filled': 0,
    'area_filled': 0,
    'city_filled': 0,
    'route_filled': 0,
    'retailer_type_filled': 0,
    'product_name_filled': 0,
    'brand_filled': 0,
    'category_filled': 0
}

data_enriched['phone_norm'] = data_enriched['phone'].apply(normalize_phone)

total_rows = len(data_enriched)
batch_size = 10000

for batch_start in range(0, total_rows, batch_size):
    batch_end = min(batch_start + batch_size, total_rows)
    print(f"   Processing rows {batch_start:,} to {batch_end:,} ({100 * batch_end / total_rows:.1f}%)")
    sys.stdout.flush()
    
    for idx in range(batch_start, batch_end):
        row = data_enriched.iloc[idx]
        phone_norm = row['phone_norm']
        base_id = row['base_id']
        name = row['name']
        area = row.get('area', '')
        city = row.get('city', '')
        brand = row.get('brand', '')
        category = row.get('category', '')
        product = row.get('product', '')
        
        # Enrich retailer information
        if phone_norm and phone_norm in phone_to_retailer:
            retailer_info = phone_to_retailer[phone_norm]
            
            # Fill retailer name if missing or "Location"
            if (name == 'Location' or pd.isna(name) or name == '') and retailer_info['retailer_name']:
                data_enriched.at[idx, 'name'] = retailer_info['retailer_name']
                improvements['retailer_name_filled'] += 1
            
            # Fill retailer type
            if retailer_info['retailer_type']:
                current_type = str(row.get('Type', '')).strip() if pd.notna(row.get('Type')) else ''
                if not current_type or current_type == '':
                    data_enriched.at[idx, 'Type'] = retailer_info['retailer_type']
                    improvements['retailer_type_filled'] += 1
            
            # Fill area
            if (pd.isna(area) or area == '') and retailer_info['area']:
                data_enriched.at[idx, 'area'] = retailer_info['area']
                improvements['area_filled'] += 1
            
            # Fill city
            if (pd.isna(city) or city == '') and retailer_info['city']:
                data_enriched.at[idx, 'city'] = retailer_info['city']
                improvements['city_filled'] += 1
        
        # Enrich product information
        if pd.notna(base_id):
            try:
                base_id_int = int(float(base_id))
                if base_id_int in base_id_to_product:
                    product_info = base_id_to_product[base_id_int]
                    
                    if (pd.isna(product) or product == '') and product_info['product_name']:
                        data_enriched.at[idx, 'product'] = product_info['product_name']
                        improvements['product_name_filled'] += 1
                    
                    if (pd.isna(brand) or brand == '') and product_info['brand']:
                        data_enriched.at[idx, 'brand'] = product_info['brand']
                        improvements['brand_filled'] += 1
                    
                    if (pd.isna(category) or category == '') and product_info['category']:
                        data_enriched.at[idx, 'category'] = product_info['category']
                        improvements['category_filled'] += 1
            except:
                pass

# Drop temporary column
data_enriched = data_enriched.drop(columns=['phone_norm'])

print(f"   [OK] Completed enriching {total_rows:,} rows")
sys.stdout.flush()

# Save enriched data
print("\n[6/7] Saving enriched data...")
sys.stdout.flush()

output_file = 'data_cleaned_enriched.csv'
data_enriched.to_csv(output_file, sep='\t', index=False, encoding='utf-8')
print(f"   [OK] Saved enriched data to {output_file}")
sys.stdout.flush()

# Print improvements summary
print("\n" + "=" * 80)
print("ENRICHMENT SUMMARY")
print("=" * 80)
print(f"Retailer name filled: {improvements['retailer_name_filled']:,}")
print(f"Area filled: {improvements['area_filled']:,}")
print(f"City filled: {improvements['city_filled']:,}")
print(f"Route filled: {improvements['route_filled']:,}")
print(f"Retailer type filled: {improvements['retailer_type_filled']:,}")
print(f"Product name filled: {improvements['product_name_filled']:,}")
print(f"Brand filled: {improvements['brand_filled']:,}")
print(f"Category filled: {improvements['category_filled']:,}")
total_improvements = sum(improvements.values())
print(f"\nTotal improvements: {total_improvements:,}")
sys.stdout.flush()

# Update dashboard_data.json
print("\n[7/7] Updating dashboard data...")
sys.stdout.flush()

try:
    with open('dashboard_data.json', 'r', encoding='utf-8') as f:
        dashboard_data = json.load(f)
    
    print("   Generating statistics from enriched data...")
    sys.stdout.flush()
    
    customer_stats = defaultdict(lambda: {
        'phone': None,
        'area': '',
        'city': '',
        'type': '',
        'total_gmv': 0.0,
        'order_count': 0,
        'unique_orders': set(),
        'item_count': 0,
        'products': defaultdict(int),
        'brands': defaultdict(int),
        'dates': set()
    })
    
    for _, row in data_enriched.iterrows():
        name = str(row['name']).strip() if pd.notna(row['name']) else 'Unknown'
        phone = int(row['phone']) if pd.notna(row['phone']) else 0
        customer_key = f"{name}_{phone}"
        
        customer = customer_stats[customer_key]
        if customer['phone'] is None:
            customer['phone'] = phone
            customer['area'] = str(row.get('area', '')).strip() if pd.notna(row.get('area')) else ''
            customer['city'] = str(row.get('city', '')).strip() if pd.notna(row.get('city')) else ''
            customer['type'] = str(row.get('Type', '')).strip() if pd.notna(row.get('Type')) else ''
        
        order_id = str(row['order_id'])
        amount = float(row['amount']) if pd.notna(row['amount']) else 0.0
        price = float(row['price_gross']) if pd.notna(row['price_gross']) else 0.0
        date = str(row['date']) if pd.notna(row['date']) else ''
        product = str(row.get('product', '')).strip() if pd.notna(row.get('product')) else ''
        brand = str(row.get('brand', '')).strip() if pd.notna(row.get('brand')) else ''
        
        customer['total_gmv'] += amount * price
        customer['order_count'] += 1
        customer['unique_orders'].add(order_id)
        customer['item_count'] += int(amount)
        customer['dates'].add(date)
        
        if product:
            customer['products'][product] += int(amount)
        if brand:
            customer['brands'][brand] += int(amount)
    
    customers_list = []
    for key, stats in customer_stats.items():
        customers_list.append({
            'name': key.split('_')[0],
            'phone': stats['phone'],
            'area': stats['area'],
            'city': stats['city'],
            'type': stats['type'],
            'total_gmv': round(stats['total_gmv'], 2),
            'order_count': stats['order_count'],
            'unique_orders': len(stats['unique_orders']),
            'item_count': stats['item_count'],
            'avg_order_value': round(stats['total_gmv'] / max(1, len(stats['unique_orders'])), 2),
            'unique_products': len(stats['products']),
            'unique_brands': len(stats['brands']),
            'unique_dates': len(stats['dates']),
            'products': dict(stats['products']),
            'brands': dict(stats['brands']),
            'orders': []
        })
    
    customers_list.sort(key=lambda x: x['total_gmv'], reverse=True)
    dashboard_data['customers'] = customers_list
    
    total_customers = len(customers_list)
    total_orders = sum(c['order_count'] for c in customers_list)
    total_gmv = sum(c['total_gmv'] for c in customers_list)
    
    print(f"   [OK] Processed {total_customers:,} customers")
    print(f"   [OK] Total orders: {total_orders:,}")
    print(f"   [OK] Total GMV: {total_gmv:,.2f}")
    sys.stdout.flush()
    
    with open('dashboard_data.json', 'w', encoding='utf-8') as f:
        json.dump(dashboard_data, f, ensure_ascii=False, indent=2)
    
    print(f"   [OK] Updated dashboard_data.json")
    sys.stdout.flush()
    
except Exception as e:
    print(f"   [ERROR] Error updating dashboard_data.json: {e}")
    import traceback
    traceback.print_exc()
    sys.stdout.flush()

print("\n" + "=" * 80)
print("ENRICHMENT COMPLETE!")
print("=" * 80)
sys.stdout.flush()


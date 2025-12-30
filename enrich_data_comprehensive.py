"""
Comprehensive Data Enrichment Script
Intelligently maps and enriches data_cleaned.csv with missing retailer and product information
"""

import pandas as pd
import numpy as np
import json
import re
import sys
from difflib import SequenceMatcher
from collections import defaultdict
import warnings
warnings.filterwarnings('ignore')

# Ensure UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

def normalize_text(text):
    """Normalize text for better matching"""
    if pd.isna(text) or text == '':
        return ''
    text = str(text).strip()
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters that might cause issues
    text = re.sub(r'[^\w\s\u0600-\u06FF]', '', text)
    return text.lower()

def normalize_phone(phone):
    """Normalize phone numbers for matching"""
    if pd.isna(phone):
        return None
    phone = str(phone).strip()
    # Remove any non-digit characters
    phone = re.sub(r'\D', '', phone)
    return phone

def similarity_score(str1, str2):
    """Calculate similarity between two strings"""
    if not str1 or not str2:
        return 0.0
    return SequenceMatcher(None, normalize_text(str1), normalize_text(str2)).ratio()

def find_best_retailer_match(phone, retailers_df):
    """Find best retailer match by phone with data quality prioritization"""
    phone_norm = normalize_phone(phone)
    if not phone_norm:
        return None
    
    # Filter by phone
    matches = retailers_df[retailers_df['phone'].astype(str).apply(normalize_phone) == phone_norm]
    
    if matches.empty:
        return None
    
    # Prioritize rows with complete data
    matches = matches.copy()
    matches['data_quality'] = (
        matches['retailer_name'].notna().astype(int) * 2 +
        matches['area'].notna().astype(int) +
        matches['city'].notna().astype(int) +
        matches['distribution_route'].notna().astype(int) +
        matches['retailer_type'].notna().astype(int)
    )
    
    # Get best match
    best_match = matches.loc[matches['data_quality'].idxmax()]
    
    return {
        'retailer_name': best_match.get('retailer_name', ''),
        'retailer_type': best_match.get('retailer_type', ''),
        'area': best_match.get('area', ''),
        'city': best_match.get('city', ''),
        'route': best_match.get('distribution_route', '')
    }

def find_best_product_match(base_id, products_df, overall_df=None):
    """Find best product match by base_id with enhanced brand extraction"""
    if pd.isna(base_id):
        return None
    
    try:
        base_id_int = int(float(base_id))
        matches = products_df[products_df['ID'] == base_id_int]
        
        if matches.empty:
            # Try to find in overall.csv as fallback
            if overall_df is not None:
                overall_matches = overall_df[overall_df['base_id'] == base_id_int]
                if not overall_matches.empty:
                    match = overall_matches.iloc[0]
                    return {
                        'product_name': str(match.get('product', '')).strip() if pd.notna(match.get('product')) else '',
                        'brand': str(match.get('brand', '')).strip() if pd.notna(match.get('brand')) else '',
                        'category': str(match.get('category', '')).strip() if pd.notna(match.get('category')) else ''
                    }
            return None
        
        # Get first match (should be unique by ID)
        match = matches.iloc[0]
        
        # Extract product name
        name = str(match.get('Name', '')).strip()
        
        # Try to extract brand (first word or two, but be smart about it)
        brand = ''
        if name:
            words = name.split()
            if len(words) > 0:
                # Common brand patterns
                first_word = words[0]
                # If first word is short, might be part of brand name
                if len(words) > 1:
                    # Check if first two words together make sense as brand
                    two_words = ' '.join(words[:2])
                    if len(two_words) <= 15:  # Reasonable brand name length
                        brand = two_words
                    else:
                        brand = first_word
                else:
                    brand = first_word
        
        # Try to get brand from overall.csv if available
        if overall_df is not None:
            overall_matches = overall_df[overall_df['base_id'] == base_id_int]
            if not overall_matches.empty:
                overall_match = overall_matches.iloc[0]
                if pd.notna(overall_match.get('brand')):
                    brand = str(overall_match.get('brand')).strip()
                if pd.notna(overall_match.get('category')):
                    category = str(overall_match.get('category')).strip()
                else:
                    category = ''
            else:
                category = ''
        else:
            category = ''
        
        return {
            'product_name': name,
            'brand': brand,
            'category': category
        }
    except Exception as e:
        return None

def enrich_from_overall(phone, base_id, overall_df):
    """Enrich data from overall.csv as reference"""
    phone_norm = normalize_phone(phone)
    if not phone_norm or overall_df.empty:
        return None
    
    # Match by phone
    phone_matches = overall_df[overall_df['phone'].astype(str).apply(normalize_phone) == phone_norm]
    
    if phone_matches.empty:
        return None
    
    # If base_id provided, try to match by both
    if not pd.isna(base_id):
        try:
            base_id_int = int(float(base_id))
            product_matches = phone_matches[phone_matches['base_id'] == base_id_int]
            if not product_matches.empty:
                match = product_matches.iloc[0]
            else:
                match = phone_matches.iloc[0]
        except:
            match = phone_matches.iloc[0]
    else:
        match = phone_matches.iloc[0]
    
    result = {}
    if 'name' in match and pd.notna(match['name']) and str(match['name']).strip() != 'Location':
        result['retailer_name'] = str(match['name']).strip()
    if 'brand' in match and pd.notna(match['brand']):
        result['brand'] = str(match['brand']).strip()
    if 'category' in match and pd.notna(match['category']):
        result['category'] = str(match['category']).strip()
    if 'product' in match and pd.notna(match['product']):
        result['product_name'] = str(match['product']).strip()
    
    return result if result else None

def main():
    print("=" * 80)
    print("COMPREHENSIVE DATA ENRICHMENT SCRIPT")
    print("=" * 80)
    sys.stdout.flush()
    
    # Load data files
    print("\n[1/7] Loading data files...")
    try:
        data_cleaned = pd.read_csv('data_cleaned.csv', sep='\t', low_memory=False, encoding='utf-8')
        print(f"   [OK] Loaded data_cleaned.csv: {len(data_cleaned):,} rows")
    except Exception as e:
        print(f"   [ERROR] Error loading data_cleaned.csv: {e}")
        return
    
    try:
        retailers_profiles = pd.read_csv('retailers_profiles.csv', sep='\t', low_memory=False, encoding='utf-8')
        # Drop empty column if exists
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
    
    # Analyze missing data
    print("\n[2/7] Analyzing missing data...")
    location_rows = data_cleaned[data_cleaned['name'] == 'Location']
    print(f"   • Rows with name='Location': {len(location_rows):,}")
    print(f"   • Unique phones with Location: {location_rows['phone'].nunique()}")
    
    missing_area = data_cleaned[data_cleaned['area'].isna() | (data_cleaned['area'] == '')]
    missing_city = data_cleaned[data_cleaned['city'].isna() | (data_cleaned['city'] == '')]
    missing_brand = data_cleaned[data_cleaned['brand'].isna() | (data_cleaned['brand'] == '')]
    missing_category = data_cleaned[data_cleaned['category'].isna() | (data_cleaned['category'] == '')]
    
    print(f"   • Rows missing area: {len(missing_area):,}")
    print(f"   • Rows missing city: {len(missing_city):,}")
    print(f"   • Rows missing brand: {len(missing_brand):,}")
    print(f"   • Rows missing category: {len(missing_category):,}")
    
    # Create enriched dataframe
    print("\n[3/7] Creating enriched dataframe...")
    data_enriched = data_cleaned.copy()
    
    # Track improvements
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
    
    # Build phone-to-retailer mapping cache
    print("\n[4/7] Building retailer mapping cache...")
    phone_to_retailer = {}
    if not retailers_profiles.empty:
        for phone in data_cleaned['phone'].unique():
            if pd.notna(phone):
                match = find_best_retailer_match(phone, retailers_profiles)
                if match:
                    phone_to_retailer[str(phone)] = match
        print(f"   [OK] Cached {len(phone_to_retailer):,} retailer mappings")
    
    # Build base_id-to-product mapping cache
    print("\n[5/7] Building product mapping cache...")
    base_id_to_product = {}
    if not base_products.empty:
        for base_id in data_cleaned['base_id'].dropna().unique():
            try:
                base_id_int = int(float(base_id))
                match = find_best_product_match(base_id_int, base_products, overall)
                if match:
                    base_id_to_product[base_id_int] = match
            except:
                pass
        print(f"   [OK] Cached {len(base_id_to_product):,} product mappings")
    
    # Enrich data row by row
    print("\n[6/7] Enriching data (this may take a while)...")
    total_rows = len(data_enriched)
    batch_size = max(1000, total_rows // 100)
    
    for idx, row in data_enriched.iterrows():
        if (idx + 1) % batch_size == 0:
            print(f"   Processing: {idx + 1:,} / {total_rows:,} rows ({100 * (idx + 1) / total_rows:.1f}%)")
        
        phone = row['phone']
        base_id = row['base_id']
        name = row['name']
        area = row.get('area', '')
        city = row.get('city', '')
        brand = row.get('brand', '')
        category = row.get('category', '')
        product = row.get('product', '')
        
        # Enrich retailer information
        if name == 'Location' or (pd.isna(name) or name == ''):
            if pd.notna(phone) and str(phone) in phone_to_retailer:
                retailer_info = phone_to_retailer[str(phone)]
                if retailer_info['retailer_name']:
                    data_enriched.at[idx, 'name'] = retailer_info['retailer_name']
                    improvements['retailer_name_filled'] += 1
                if retailer_info['retailer_type']:
                    data_enriched.at[idx, 'Type'] = retailer_info['retailer_type']
                    improvements['retailer_type_filled'] += 1
        
        # Enrich area, city, route
        if pd.notna(phone) and str(phone) in phone_to_retailer:
            retailer_info = phone_to_retailer[str(phone)]
            if (pd.isna(area) or area == '') and retailer_info['area']:
                data_enriched.at[idx, 'area'] = retailer_info['area']
                improvements['area_filled'] += 1
            if (pd.isna(city) or city == '') and retailer_info['city']:
                data_enriched.at[idx, 'city'] = retailer_info['city']
                improvements['city_filled'] += 1
        
        # Enrich product information from base-products
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
        
        # Enrich from overall.csv as reference
        if not overall.empty and pd.notna(phone):
            overall_info = enrich_from_overall(phone, base_id, overall)
            if overall_info:
                if 'retailer_name' in overall_info and (name == 'Location' or pd.isna(name) or name == ''):
                    data_enriched.at[idx, 'name'] = overall_info['retailer_name']
                    improvements['retailer_name_filled'] += 1
                if 'brand' in overall_info and (pd.isna(brand) or brand == ''):
                    data_enriched.at[idx, 'brand'] = overall_info['brand']
                    improvements['brand_filled'] += 1
                if 'category' in overall_info and (pd.isna(category) or category == ''):
                    data_enriched.at[idx, 'category'] = overall_info['category']
                    improvements['category_filled'] += 1
                if 'product_name' in overall_info and (pd.isna(product) or product == ''):
                    data_enriched.at[idx, 'product'] = overall_info['product_name']
                    improvements['product_name_filled'] += 1
    
    print(f"   [OK] Completed enriching {total_rows:,} rows")
    
    # Save enriched data
    print("\n[7/7] Saving enriched data...")
    output_file = 'data_cleaned_enriched.csv'
    data_enriched.to_csv(output_file, sep='\t', index=False)
    print(f"   [OK] Saved enriched data to {output_file}")
    
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
    
    # Update dashboard_data.json
    print("\n" + "=" * 80)
    print("UPDATING DASHBOARD DATA")
    print("=" * 80)
    
    try:
        # Load existing dashboard data
        with open('dashboard_data.json', 'r', encoding='utf-8') as f:
            dashboard_data = json.load(f)
        
        # Generate new statistics from enriched data
        print("\nGenerating statistics from enriched data...")
        
        # Group by customer (name + phone)
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
            'dates': set(),
            'orders': []
        })
        
        # Process enriched data
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
        
        # Convert to dashboard format
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
                'orders': []  # Simplified for now
            })
        
        # Sort by total_gmv descending
        customers_list.sort(key=lambda x: x['total_gmv'], reverse=True)
        
        # Update dashboard data
        dashboard_data['customers'] = customers_list
        
        # Calculate summary statistics
        total_customers = len(customers_list)
        total_orders = sum(c['order_count'] for c in customers_list)
        total_gmv = sum(c['total_gmv'] for c in customers_list)
        
        print(f"   [OK] Processed {total_customers:,} customers")
        print(f"   [OK] Total orders: {total_orders:,}")
        print(f"   [OK] Total GMV: {total_gmv:,.2f}")
        
        # Save updated dashboard data
        with open('dashboard_data.json', 'w', encoding='utf-8') as f:
            json.dump(dashboard_data, f, ensure_ascii=False, indent=2)
        
        print(f"   [OK] Updated dashboard_data.json")
        
    except Exception as e:
        print(f"   [ERROR] Error updating dashboard_data.json: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("ENRICHMENT COMPLETE!")
    print("=" * 80)

if __name__ == '__main__':
    main()


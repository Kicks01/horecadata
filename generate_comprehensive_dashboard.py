#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
import json
from collections import defaultdict
from datetime import datetime
import statistics
import re

# Area/City Normalization Mapping
AREA_CITY_MAPPING = {
    # Cairo Governorate variations
    'المعصرة': ('المعصرة', 'محافظة القاهرة'),
    'مدينة نصر‎‎‎‎': ('مدينة نصر', 'محافظة القاهرة'),
    'مدينة نصر': ('مدينة نصر', 'محافظة القاهرة'),
    'الزهراء': ('الزهراء', 'محافظة القاهرة'),
    'النزهة': ('النزهة', 'محافظة القاهرة'),
    'El-Nozha': ('النزهة', 'محافظة القاهرة'),
    'Nasr City': ('مدينة نصر', 'محافظة القاهرة'),
    'Cairo Governorate': ('غير محدد', 'محافظة القاهرة'),
    'الإسكندرية': ('الإسكندرية', 'محافظة الإسكندرية'),
    'Alexandria Governorate': ('الإسكندرية', 'محافظة الإسكندرية'),
    'الجيزة': ('الجيزة', 'محافظة الجيزة'),
    'Giza Governorate': ('الجيزة', 'محافظة الجيزة'),
    'القليوبية': ('القليوبية', 'محافظة القليوبية'),
    'Al-Qalyubia Governorate': ('القليوبية', 'محافظة القليوبية'),
    'الدقهلية': ('الدقهلية', 'محافظة الدقهلية'),
    'Dakahlia Governorate': ('الدقهلية', 'محافظة الدقهلية'),
    'الشرقية': ('الشرقية', 'محافظة الشرقية'),
    'Al-Sharqia Governorate': ('الشرقية', 'محافظة الشرقية'),
    'السويس': ('السويس', 'محافظة السويس'),
    'Suez Governorate': ('السويس', 'محافظة السويس'),
    'المنوفية': ('المنوفية', 'محافظة المنوفية'),
    'Menofia Governorate': ('المنوفية', 'محافظة المنوفية'),
    'البحيرة': ('البحيرة', 'محافظة البحيرة'),
    'Beheira Governorate': ('البحيرة', 'محافظة البحيرة'),
    'الفيوم': ('الفيوم', 'محافظة الفيوم'),
    'Faiyum Governorate': ('الفيوم', 'محافظة الفيوم'),
    'قنا': ('قنا', 'محافظة قنا'),
    'Qena Governorate': ('قنا', 'محافظة قنا'),
    'الإسماعيلية': ('الإسماعيلية', 'محافظة الإسماعيلية'),
    'Ismailia Governorate': ('الإسماعيلية', 'محافظة الإسماعيلية'),
    'الغربية': ('الغربية', 'محافظة الغربية'),
    'Gharbia Governorate': ('الغربية', 'محافظة الغربية'),
}

def normalize_area_city(area, city):
    """Normalize area and city values using mapping"""
    if pd.isna(area) or str(area).strip() == '' or str(area) == 'غير محدد':
        area = 'غير محدد'
    else:
        area = str(area).strip()
        # Look up in mapping
        if area in AREA_CITY_MAPPING:
            area, city_mapped = AREA_CITY_MAPPING[area]
            city = city_mapped if pd.isna(city) else city
        
    if pd.isna(city) or str(city).strip() == '' or str(city) == 'غير محدد':
        city = 'غير محدد'
    else:
        city = str(city).strip()
        # If city is in mapping keys, normalize it
        if city in AREA_CITY_MAPPING:
            _, city = AREA_CITY_MAPPING[city]
    
    return area, city

# Customer Segmentation Function
def classify_customer(customer):
    """
    Classify customers into segments based on their behavior and value
    """
    gmv = customer['total_gmv']
    orders = customer['unique_orders']
    avg_value = customer['avg_order_value']
    unique_dates = customer['unique_dates']
    
    # Calculate metrics
    frequency_score = min(unique_dates / 30, 1) * 100 if unique_dates > 0 else 0  # Activity frequency
    value_score = min(gmv / 100000, 1) * 100  # Monetary value
    order_consistency = min(orders / 100, 1) * 100  # Order consistency
    
    # High Value Customer: Top 10% by GMV
    if gmv > 1000000:
        return {'segment': 'عميل مميز', 'color': '#4ade80', 'reason': 'قيمة GMV عالية جداً'}
    
    # Premium Customer: Top 25% by GMV
    if gmv > 500000:
        return {'segment': 'عميل فئة أولى', 'color': '#60a5fa', 'reason': 'قيمة GMV عالية'}
    
    # Loyal Customer: Many orders with consistent purchases
    if orders > 200 and frequency_score > 70:
        return {'segment': 'عميل وفي', 'color': '#34d399', 'reason': 'عدد طلبات عالي مع انتظام'}
    
    # Growing Customer: Increasing trend (reasonable orders and value)
    if orders > 50 and gmv > 100000 and avg_value > 1000:
        return {'segment': 'عميل متنامي', 'color': '#fbbf24', 'reason': 'نمو تدريجي في القيمة والطلبات'}
    
    # Potential Customer: Low frequency but good order value
    if avg_value > 500 and orders > 10:
        return {'segment': 'عميل واعد', 'color': '#f97316', 'reason': 'قيمة طلب عالية مع أوامر محدودة'}
    
    # Active Customer: Regular orders
    if orders > 50:
        return {'segment': 'عميل نشط', 'color': '#8b5cf6', 'reason': 'عدد طلبات جيد'}
    
    # Occasional Customer: Few orders but reasonable value
    if orders > 10 and gmv > 10000:
        return {'segment': 'عميل عارض', 'color': '#a78bfa', 'reason': 'طلبات قليلة لكن بقيم جيدة'}
    
    # New Customer: Just starting
    if orders <= 10:
        return {'segment': 'عميل جديد', 'color': '#71717a', 'reason': 'عدد طلبات قليل جداً'}
    
    # Default
    return {'segment': 'عميل عادي', 'color': '#9ca3af', 'reason': 'عميل قياسي'}

# Read the cleaned data
df = pd.read_csv('data_cleaned.csv', sep='\t', encoding='utf-8')

# Process customer data
customers_data = defaultdict(lambda: {
    'phone': '',
    'area': '',
    'city': '',
    'type': '',
    'orders_grouped': defaultdict(lambda: {'date': '', 'items': []}),
    'products': defaultdict(int),
    'brands': defaultdict(int),
    'total_gmv': 0,
    'item_count': 0,
    'dates': set()
})

# Group by customer name
for _, row in df.iterrows():
    customer_name = row['name']
    
    customers_data[customer_name]['phone'] = row['phone']
    customers_data[customer_name]['area'] = row['area'] if pd.notna(row['area']) else 'غير محدد'
    customers_data[customer_name]['city'] = row['city'] if pd.notna(row['city']) else 'غير محدد'
    customers_data[customer_name]['type'] = row['Type'] if pd.notna(row['Type']) else 'غير محدد'
    
    # Track unique orders grouped by order_id
    order_id = str(row['order_id'])
    
    # Add item to order
    item_data = {
        'product': str(row['product']),
        'brand': str(row['brand']),
        'quantity': float(row['amount']),
        'price': float(row['price_gross']),
        'total': float(row['amount']) * float(row['price_gross'])
    }
    
    customers_data[customer_name]['orders_grouped'][order_id]['date'] = str(row['date'])
    customers_data[customer_name]['orders_grouped'][order_id]['items'].append(item_data)
    customers_data[customer_name]['dates'].add(str(row['date']))
    
    # Track products
    product = str(row['product'])
    customers_data[customer_name]['products'][product] += 1
    
    # Track brands
    brand = str(row['brand'])
    customers_data[customer_name]['brands'][brand] += 1
    
    # Calculate GMV and count items
    gmv = float(row['amount']) * float(row['price_gross'])
    customers_data[customer_name]['total_gmv'] += gmv
    customers_data[customer_name]['item_count'] += 1

# Convert to list and sort by GMV
customers_list = []
for name, data in customers_data.items():
    # Convert orders_grouped dict to list
    orders_list = []
    for order_id, order_info in sorted(data['orders_grouped'].items(), key=lambda x: x[1]['date'], reverse=True):
        orders_list.append({
            'order_id': order_id,
            'date': order_info['date'],
            'items': order_info['items']
        })
    
    unique_order_count = len(orders_list)
    avg_order_value = data['total_gmv'] / unique_order_count if unique_order_count > 0 else 0
    unique_dates = len(data['dates'])
    
    customer_obj = {
        'name': name,
        'phone': data['phone'],
        'area': data['area'],
        'city': data['city'],
        'type': data['type'],
        'total_gmv': round(data['total_gmv'], 2),
        'unique_orders': unique_order_count,
        'item_count': data['item_count'],
        'unique_products': len(data['products']),
        'unique_brands': len(data['brands']),
        'unique_dates': unique_dates,
        'avg_order_value': round(avg_order_value, 2),
        'products': dict(data['products']),
        'brands': dict(data['brands']),
        'orders': orders_list
    }
    
    # Customer Segmentation
    segmentation = classify_customer(customer_obj)
    customer_obj['segment'] = segmentation['segment']
    customer_obj['segment_color'] = segmentation['color']
    customer_obj['segment_reason'] = segmentation['reason']
    
    customers_list.append(customer_obj)

customers_list.sort(key=lambda x: x['total_gmv'], reverse=True)

# Get summary stats
total_customers = len(customers_list)
total_gmv = sum(c['total_gmv'] for c in customers_list)
total_unique_orders = sum(c['unique_orders'] for c in customers_list)
total_items = sum(c['item_count'] for c in customers_list)
unique_products = len(df['product'].unique())
unique_brands = len(df['brand'].unique())

# Group by Area (Top 10 customers per area)
area_groups = defaultdict(list)
for customer in customers_list:
    area = customer['area']
    area_groups[area].append(customer)

# Sort each area by GMV and get top 10
for area in area_groups:
    area_groups[area] = sorted(area_groups[area], key=lambda x: x['total_gmv'], reverse=True)[:10]

# Convert to list format for JavaScript with aggregated data
area_groups_sorted = []
for area, customers in sorted(area_groups.items(), key=lambda x: sum(c['total_gmv'] for c in x[1]), reverse=True):
    area_groups_sorted.append({
        'name': area,
        'customers': customers,
        'gmv': sum(c['total_gmv'] for c in customers)
    })

# Group by City (Top 50 customers per city)
city_groups = defaultdict(list)
for customer in customers_list:
    city = customer['city']
    city_groups[city].append(customer)

# Sort each city by GMV and get top 50
for city in city_groups:
    city_groups[city] = sorted(city_groups[city], key=lambda x: x['total_gmv'], reverse=True)[:50]

# Convert to list format for JavaScript with aggregated data
city_groups_sorted = []
for city, customers in sorted(city_groups.items(), key=lambda x: sum(c['total_gmv'] for c in x[1]), reverse=True):
    city_groups_sorted.append({
        'name': city,
        'customers': customers,
        'gmv': sum(c['total_gmv'] for c in customers)
    })

# Customer Segments Analysis
segments_count = defaultdict(int)
segments_gmv = defaultdict(float)
segment_colors = {
    'عميل مميز': '#4ade80',
    'عميل فئة أولى': '#60a5fa',
    'عميل وفي': '#34d399',
    'عميل متنامي': '#fbbf24',
    'عميل واعد': '#f97316',
    'عميل نشط': '#8b5cf6',
    'عميل عارض': '#a78bfa',
    'عميل جديد': '#ec4899',
    'عميل عادي': '#64748b'
}

for customer in customers_list:
    seg = customer['segment']
    segments_count[seg] += 1
    segments_gmv[seg] += customer['total_gmv']

# Create segments distribution list for JavaScript
segments_distribution = []
for segment in segment_colors.keys():
    if segment in segments_count:
        segments_distribution.append({
            'name': segment,
            'color': segment_colors[segment],
            'count': segments_count[segment],
            'gmv': segments_gmv[segment]
        })

# Top Areas by GMV
top_areas_by_gmv = sorted([(area, sum(c['total_gmv'] for c in customers)) for area, customers in area_groups.items()], 
                           key=lambda x: x[1], reverse=True)[:10]

# Top Cities by GMV
top_cities_by_gmv = sorted([(city, sum(c['total_gmv'] for c in customers)) for city, customers in city_groups.items()], 
                            key=lambda x: x[1], reverse=True)[:10]

# Average metrics
avg_gmv = total_gmv / total_customers if total_customers > 0 else 0
avg_orders = total_unique_orders / total_customers if total_customers > 0 else 0

print(f"Total Customers: {total_customers}")
print(f"Total GMV: {total_gmv:,.2f}")
print(f"Total Unique Orders: {total_unique_orders:,}")
print(f"Total Items: {total_items:,}")
print(f"Unique Products: {unique_products:,}")
print(f"Unique Brands: {unique_brands:,}")
print(f"Average GMV per Customer: {avg_gmv:,.2f}")

# Generate HTML
html = '''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تحليل بيانات Horeca الشامل - لوحة التحكم المتقدمة</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@300;400;600;700;900&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Cairo', sans-serif;
            background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
            min-height: 100vh;
            padding: 20px;
            direction: rtl;
            color: #fafafa;
        }

        .container {
            max-width: 1800px;
            margin: 0 auto;
        }

        .header {
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }

        .header h1 {
            color: #fafafa;
            font-size: 2.5rem;
            font-weight: 900;
            margin-bottom: 10px;
        }

        .header p {
            color: #a1a1aa;
            font-size: 1.1rem;
        }

        .stats-overview {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        }

        .stat-card h3 {
            color: #a1a1aa;
            font-size: 0.85rem;
            margin-bottom: 10px;
            font-weight: 600;
        }

        .stat-card .value {
            color: #fafafa;
            font-size: 1.8rem;
            font-weight: 700;
        }

        .segment-section {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }

        .segment-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        }

        .segment-header h2 {
            color: #fafafa;
            font-size: 1.8rem;
            font-weight: 700;
        }

        .customers-table-container {
            overflow-x: auto;
            margin-top: 20px;
        }

        .customers-table {
            width: 100%;
            border-collapse: collapse;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 10px;
            overflow: hidden;
        }

        .customers-table thead {
            background: rgba(255, 255, 255, 0.1);
        }

        .customers-table th {
            padding: 15px;
            text-align: right;
            color: #fafafa;
            font-weight: 700;
            font-size: 0.9rem;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        }

        .customers-table td {
            padding: 12px 15px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            color: #e4e4e7;
            font-size: 0.9rem;
        }

        .customers-table tbody tr:hover {
            background: rgba(255, 255, 255, 0.05);
        }

        .customer-detail-row {
            background: rgba(255, 255, 255, 0.02);
        }

        .customer-detail-row td {
            padding: 20px;
        }

        .customer-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }

        .detail-group {
            background: rgba(255, 255, 255, 0.03);
            padding: 15px;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .detail-group h4 {
            color: #a1a1aa;
            font-size: 0.85rem;
            margin-bottom: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .detail-item {
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            padding: 5px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.02);
        }

        .detail-item label {
            color: #71717a;
            font-size: 0.85rem;
        }

        .detail-item .value {
            color: #fafafa;
            font-weight: 600;
        }

        .toggle-details {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.3);
            padding: 8px 15px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85rem;
            transition: all 0.3s ease;
            font-family: 'Cairo', sans-serif;
        }

        .toggle-details:hover {
            background: rgba(59, 130, 246, 0.3);
        }

        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .badge-premium {
            background: rgba(34, 197, 94, 0.2);
            color: #4ade80;
        }

        .badge-standard {
            background: rgba(251, 191, 36, 0.2);
            color: #fbbf24;
        }

        .badge-low {
            background: rgba(239, 68, 68, 0.2);
            color: #f87171;
        }

        .customer-segment-badge {
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
            text-align: center;
        }

        .search-filter {
            margin-bottom: 20px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
        }

        .search-input {
            flex: 1;
            min-width: 250px;
            padding: 12px 20px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            color: #fafafa;
            font-size: 0.9rem;
            font-family: 'Cairo', sans-serif;
        }

        .search-input::placeholder {
            color: #71717a;
        }

        .search-input:focus {
            outline: none;
            border-color: rgba(255, 255, 255, 0.3);
            background: rgba(255, 255, 255, 0.08);
        }

        .pagination {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-top: 25px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
        }

        .pagination button {
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.3);
            padding: 8px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.85rem;
            font-family: 'Cairo', sans-serif;
            transition: all 0.3s ease;
        }

        .pagination button:hover {
            background: rgba(59, 130, 246, 0.3);
        }

        .pagination button.active {
            background: rgba(59, 130, 246, 0.5);
            border-color: rgba(59, 130, 246, 0.8);
            color: #ffffff;
        }

        .pagination button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .pagination .page-info {
            color: #a1a1aa;
            font-size: 0.9rem;
            padding: 8px 12px;
        }

        .products-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }

        .product-item {
            background: rgba(255, 255, 255, 0.02);
            padding: 10px;
            border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 0.8rem;
        }

        .product-name {
            color: #fafafa;
            font-weight: 600;
            margin-bottom: 3px;
        }

        .product-count {
            color: #60a5fa;
            font-size: 0.75rem;
        }

        .brands-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
            gap: 10px;
            margin-top: 10px;
        }

        .brand-item {
            background: rgba(255, 255, 255, 0.02);
            padding: 10px;
            border-radius: 6px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            font-size: 0.8rem;
        }

        .brand-name {
            color: #fafafa;
            font-weight: 600;
            margin-bottom: 3px;
        }

        .brand-count {
            color: #4ade80;
            font-size: 0.75rem;
        }

        .expandable-section {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            margin-top: 20px;
            overflow: hidden;
        }

        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
            background: rgba(255, 255, 255, 0.02);
        }

        .section-header:hover {
            background: rgba(255, 255, 255, 0.05);
        }

        .section-title {
            color: #fafafa;
            font-weight: 600;
            font-size: 0.95rem;
        }

        .section-toggle {
            color: #60a5fa;
            transition: transform 0.3s ease;
            font-size: 0.8rem;
        }

        .expandable-section.expanded .section-toggle {
            transform: rotate(90deg);
        }

        .section-content {
            padding: 15px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
        }

        .section-content.hidden {
            display: none;
        }

        .order-container {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 6px;
            margin-bottom: 15px;
            overflow: hidden;
        }

        .order-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 15px;
            background: rgba(59, 130, 246, 0.1);
            cursor: pointer;
            transition: all 0.3s ease;
            border-left: 4px solid #60a5fa;
        }

        .order-header:hover {
            background: rgba(59, 130, 246, 0.2);
        }

        .order-id-date {
            display: flex;
            align-items: center;
            gap: 15px;
            flex: 1;
        }

        .order-label {
            color: #71717a;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .order-value {
            color: #fafafa;
            font-weight: 700;
            font-size: 0.9rem;
        }

        .expand-arrow {
            color: #60a5fa;
            transition: transform 0.3s ease;
            font-size: 0.75rem;
            margin-left: 10px;
        }

        .order-container.expanded .expand-arrow {
            transform: rotate(180deg);
        }

        .order-items-container {
            padding: 15px;
            border-top: 1px solid rgba(255, 255, 255, 0.05);
            background: rgba(255, 255, 255, 0.01);
        }

        .order-items-container.hidden {
            display: none;
        }

        .order-item {
            background: rgba(255, 255, 255, 0.03);
            padding: 12px;
            border-radius: 6px;
            margin-bottom: 10px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 12px;
            font-size: 0.85rem;
            border-left: 3px solid rgba(59, 130, 246, 0.5);
        }

        .item-field {
            display: flex;
            flex-direction: column;
        }

        .item-label {
            color: #71717a;
            font-size: 0.75rem;
            margin-bottom: 3px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .item-value {
            color: #fafafa;
            font-weight: 600;
        }

        .orders-list {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .hidden {
            display: none;
        }

        .group-table-container {
            overflow-x: auto;
            margin-top: 20px;
        }

        .group-table {
            width: 100%;
            border-collapse: collapse;
            background: rgba(255, 255, 255, 0.03);
            border-radius: 10px;
            overflow: hidden;
        }

        .group-table thead {
            background: rgba(255, 255, 255, 0.1);
        }

        .group-table th {
            padding: 12px 15px;
            text-align: right;
            color: #fafafa;
            font-weight: 700;
            font-size: 0.85rem;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        }

        .group-table td {
            padding: 10px 15px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            color: #e4e4e7;
            font-size: 0.85rem;
        }

        .group-table tbody tr:hover {
            background: rgba(255, 255, 255, 0.05);
        }

        .segment-distribution {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }

        .segment-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 20px;
            transition: all 0.3s ease;
        }

        .segment-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        }

        .segment-card-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 15px;
            padding-bottom: 12px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        }

        .segment-badge-color {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            flex-shrink: 0;
        }

        .segment-card h4 {
            color: #fafafa;
            font-weight: 700;
            font-size: 0.95rem;
            margin-bottom: 3px;
        }

        .segment-card-stat {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
            padding: 8px 0;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        .segment-card-stat label {
            color: #a1a1aa;
            font-size: 0.8rem;
            font-weight: 600;
        }

        .segment-card-stat .value {
            color: #fafafa;
            font-weight: 700;
            font-size: 1.1rem;
        }

        .segment-card-stat .percentage {
            color: #60a5fa;
            font-weight: 600;
            font-size: 0.85rem;
        }

        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.8rem;
            }
            .segment-header {
                flex-direction: column;
                align-items: flex-start;
            }
            .customers-table {
                font-size: 0.8rem;
            }
            .customers-table td, .customers-table th {
                padding: 8px;
            }
            .customer-details {
                grid-template-columns: 1fr;
            }
            .order-item {
                grid-template-columns: 1fr;
            }
            .segment-distribution {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>تحليل بيانات Horeca الشامل والمتقدم</h1>
            <p>لوحة تحكم كاملة لجميع العملاء مع تحليل تفصيلي للطلبات والمنتجات والعلامات التجارية</p>
        </div>

        <div class="stats-overview">
            <div class="stat-card">
                <h3>إجمالي العملاء</h3>
                <div class="value">''' + str(total_customers) + '''</div>
            </div>
            <div class="stat-card">
                <h3>إجمالي المبيعات (GMV)</h3>
                <div class="value">''' + f"{total_gmv:,.0f}" + ''' EGP</div>
            </div>
            <div class="stat-card">
                <h3>إجمالي الطلبات الفريدة</h3>
                <div class="value">''' + f"{total_unique_orders:,}" + '''</div>
            </div>
            <div class="stat-card">
                <h3>المنتجات الفريدة</h3>
                <div class="value">''' + f"{unique_products:,}" + '''</div>
            </div>
            <div class="stat-card">
                <h3>العلامات التجارية</h3>
                <div class="value">''' + f"{unique_brands:,}" + '''</div>
            </div>
        </div>

        <div class="stats-overview">
            <div class="stat-card">
                <h3>متوسط GMV لكل عميل</h3>
                <div class="value">''' + f"{avg_gmv:,.0f}" + ''' EGP</div>
            </div>
            <div class="stat-card">
                <h3>متوسط الطلبات لكل عميل</h3>
                <div class="value">''' + f"{avg_orders:.1f}" + '''</div>
            </div>
            <div class="stat-card">
                <h3>إجمالي المنتجات (مع التكرار)</h3>
                <div class="value">''' + f"{total_items:,}" + '''</div>
            </div>
            <div class="stat-card">
                <h3>عدد المناطق</h3>
                <div class="value">''' + str(len(area_groups)) + '''</div>
            </div>
            <div class="stat-card">
                <h3>عدد المدن</h3>
                <div class="value">''' + str(len(city_groups)) + '''</div>
            </div>
        </div>

        <div class="segment-section">
            <div class="segment-header">
                <h2>� تحليل العملاء حسب المنطقة (أفضل 10 عملاء لكل منطقة)</h2>
            </div>
            <div class="group-table-container">
                <table class="group-table">
                    <thead>
                        <tr>
                            <th>المنطقة</th>
                            <th>عدد العملاء</th>
                            <th>إجمالي GMV</th>
                            <th>متوسط GMV للعميل</th>
                            <th>أفضل عميل</th>
                            <th>GMV أفضل عميل</th>
                        </tr>
                    </thead>
                    <tbody id="areaTableBody">
                    </tbody>
                </table>
            </div>
        </div>

        <div class="segment-section">
            <div class="segment-header">
                <h2>🏙️ تحليل العملاء حسب المدينة (أفضل 50 عميل لكل مدينة)</h2>
            </div>
            <div class="group-table-container">
                <table class="group-table">
                    <thead>
                        <tr>
                            <th>المدينة</th>
                            <th>عدد العملاء</th>
                            <th>إجمالي GMV</th>
                            <th>متوسط GMV للعميل</th>
                            <th>أفضل عميل</th>
                            <th>GMV أفضل عميل</th>
                        </tr>
                    </thead>
                    <tbody id="cityTableBody">
                    </tbody>
                </table>
            </div>
        </div>

        <div class="segment-section">
            <div class="segment-header">
                <h2>📈 توزيع العملاء حسب التصنيف</h2>
            </div>
            <div class="segment-distribution" id="segmentDistribution">
            </div>
        </div>

        <div class="segment-section">
            <div class="segment-header">
                <h2>�📊 تحليل شامل لجميع العملاء</h2>
            </div>
            <div class="search-filter">
                <input type="text" class="search-input" id="customerSearch" placeholder="🔍 ابحث عن العميل...">
            </div>
            <div class="customers-table-container">
                <table class="customers-table" id="customersTable">
                    <thead>
                        <tr>
                            <th>اسم العميل</th>
                            <th>التصنيف</th>
                            <th>الهاتف</th>
                            <th>النوع</th>
                            <th>المدينة</th>
                            <th>المنطقة</th>
                            <th>إجمالي GMV</th>
                            <th>الطلبات الفريدة</th>
                            <th>التفاصيل</th>
                        </tr>
                    </thead>
                    <tbody id="customersTableBody">
                    </tbody>
                </table>
            </div>
            <div class="pagination" id="paginationContainer"></div>
        </div>
    </div>

    <script src="dashboard_data.js"></script>
    <script>
        const itemsPerPage = 25;
        let currentPage = 1;
        let filteredData = [];

        // Initialize data from external file
        function initializeData() {
            try {
                // Check if data is loaded from external script
                // The variables are defined as const in dashboard_data.js
                if (typeof customersData !== 'undefined' && Array.isArray(customersData) && customersData.length > 0) {
                    // Data is already loaded, just set filteredData
                    filteredData = [...customersData];
                    return true;
                }
            } catch (e) {
                // Variables not loaded yet
            }
            return false;
        }

        // Wait for data to load
        function waitForDataAndRender() {
            if (initializeData()) {
                renderAreaGroupsTable();
                renderCityGroupsTable();
                renderSegmentDistribution();
                renderTable();
            } else {
                setTimeout(waitForDataAndRender, 100);
            }
        }

        // Render Area Groups Table
        function renderAreaGroupsTable() {
            const tbody = document.getElementById('areaTableBody');
            if (!tbody) return;
            tbody.innerHTML = '';
            
            if (!areaGroupsData || areaGroupsData.length === 0) return;
            
            areaGroupsData.forEach(area => {
                const row = document.createElement('tr');
                const avgGmv = area.customers.length > 0 ? area.gmv / area.customers.length : 0;
                const topCustomer = area.customers.length > 0 ? area.customers[0] : null;
                
                row.innerHTML = `
                    <td>${area.name}</td>
                    <td>${area.customers.length}</td>
                    <td>${area.gmv.toLocaleString('ar')} EGP</td>
                    <td>${avgGmv.toLocaleString('ar', {maximumFractionDigits: 0})} EGP</td>
                    <td>${topCustomer ? topCustomer.name : 'N/A'}</td>
                    <td>${topCustomer ? topCustomer.total_gmv.toLocaleString('ar') : '0'} EGP</td>
                `;
                tbody.appendChild(row);
            });
        }

        // Render City Groups Table
        function renderCityGroupsTable() {
            const tbody = document.getElementById('cityTableBody');
            if (!tbody) return;
            tbody.innerHTML = '';
            
            if (!cityGroupsData || cityGroupsData.length === 0) return;
            
            cityGroupsData.forEach(city => {
                const row = document.createElement('tr');
                const avgGmv = city.customers.length > 0 ? city.gmv / city.customers.length : 0;
                const topCustomer = city.customers.length > 0 ? city.customers[0] : null;
                
                row.innerHTML = `
                    <td>${city.name}</td>
                    <td>${city.customers.length}</td>
                    <td>${city.gmv.toLocaleString('ar')} EGP</td>
                    <td>${avgGmv.toLocaleString('ar', {maximumFractionDigits: 0})} EGP</td>
                    <td>${topCustomer ? topCustomer.name : 'N/A'}</td>
                    <td>${topCustomer ? topCustomer.total_gmv.toLocaleString('ar') : '0'} EGP</td>
                `;
                tbody.appendChild(row);
            });
        }

        // Render Segment Distribution Cards
        function renderSegmentDistribution() {
            const container = document.getElementById('segmentDistribution');
            if (!container) return;
            container.innerHTML = '';
            
            if (!segmentsData || segmentsData.length === 0) return;
            
            const totalCustomers = customersData.length;
            
            segmentsData.forEach(segment => {
                const percentage = ((segment.count / totalCustomers) * 100).toFixed(1);
                const card = document.createElement('div');
                card.className = 'segment-card';
                card.innerHTML = `
                    <div class="segment-card-header">
                        <div class="segment-badge-color" style="background-color: ${segment.color};"></div>
                        <div>
                            <h4>${segment.name}</h4>
                        </div>
                    </div>
                    <div class="segment-card-stat">
                        <label>عدد العملاء</label>
                        <div class="value">${segment.count}</div>
                    </div>
                    <div class="segment-card-stat">
                        <label>النسبة المئوية</label>
                        <div class="percentage">${percentage}%</div>
                    </div>
                    <div class="segment-card-stat">
                        <label>إجمالي GMV</label>
                        <div class="value" style="font-size: 0.95rem;">${segment.gmv.toLocaleString('ar', {maximumFractionDigits: 0})} EGP</div>
                    </div>
                    <div class="segment-card-stat">
                        <label>متوسط GMV</label>
                        <div class="value" style="font-size: 0.95rem;">${(segment.gmv / segment.count).toLocaleString('ar', {maximumFractionDigits: 0})} EGP</div>
                    </div>
                `;
                container.appendChild(card);
            });
        }

        function renderTable() {
            const tbody = document.getElementById('customersTableBody');
            if (!tbody) return;
            tbody.innerHTML = '';

            if (!filteredData || filteredData.length === 0) return;

            const startIdx = (currentPage - 1) * itemsPerPage;
            const endIdx = startIdx + itemsPerPage;
            const pageData = filteredData.slice(startIdx, endIdx);

            pageData.forEach((customer, idx) => {
                const globalIdx = startIdx + idx;
                
                // Main row
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${customer.name}</td>
                    <td><span class="customer-segment-badge" style="background: ${customer.segment_color}40; color: ${customer.segment_color}; border: 1px solid ${customer.segment_color};">${customer.segment}</span></td>
                    <td>${customer.phone || 'غير محدد'}</td>
                    <td><span class="badge badge-premium">${customer.type}</span></td>
                    <td>${customer.city}</td>
                    <td>${customer.area}</td>
                    <td>${customer.total_gmv.toLocaleString('ar')} EGP</td>
                    <td>${customer.unique_orders}</td>
                    <td><button class="toggle-details" onclick="toggleDetails(${globalIdx})">عرض التفاصيل</button></td>
                `;
                tbody.appendChild(row);

                // Detail row
                const detailRow = document.createElement('tr');
                detailRow.className = 'customer-detail-row hidden';
                detailRow.id = `detail-${globalIdx}`;
                
                const productsHtml = Object.entries(customer.products)
                    .sort((a, b) => b[1] - a[1])
                    .map(([prod, count]) => `<div class="product-item"><div class="product-name">${prod}</div><div class="product-count">طلبات: ${count}</div></div>`)
                    .join('');

                const brandsHtml = Object.entries(customer.brands)
                    .sort((a, b) => b[1] - a[1])
                    .map(([brand, count]) => `<div class="brand-item"><div class="brand-name">${brand}</div><div class="brand-count">طلبات: ${count}</div></div>`)
                    .join('');

                const ordersHtml = customer.orders.slice(0, 30).map((order, orderIdx) => `
                    <div class="order-container">
                        <div class="order-header" onclick="toggleOrderItems(${globalIdx}, ${orderIdx}, event)">
                            <div class="order-id-date">
                                <div class="order-label">رقم الطلب:</div>
                                <div class="order-value">${order.order_id}</div>
                                <div class="order-label" style="margin-right: 20px;">التاريخ:</div>
                                <div class="order-value">${order.date}</div>
                            </div>
                            <div class="expand-arrow" id="arrow-${globalIdx}-${orderIdx}">▼</div>
                        </div>
                        <div class="order-items-container hidden" id="items-${globalIdx}-${orderIdx}">
                            ${order.items.map(item => `
                                <div class="order-item">
                                    <div class="item-field">
                                        <div class="item-label">المنتج</div>
                                        <div class="item-value">${item.product}</div>
                                    </div>
                                    <div class="item-field">
                                        <div class="item-label">العلامة</div>
                                        <div class="item-value">${item.brand}</div>
                                    </div>
                                    <div class="item-field">
                                        <div class="item-label">الكمية</div>
                                        <div class="item-value">${item.quantity}</div>
                                    </div>
                                    <div class="item-field">
                                        <div class="item-label">السعر</div>
                                        <div class="item-value">${item.price} EGP</div>
                                    </div>
                                    <div class="item-field">
                                        <div class="item-label">الإجمالي</div>
                                        <div class="item-value">${item.total.toLocaleString('ar')} EGP</div>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `).join('');

                detailRow.innerHTML = `
                    <td colspan="9">
                        <div class="customer-details">
                            <div class="detail-group">
                                <h4>📋 بيانات العميل</h4>
                                <div class="detail-item">
                                    <label>الاسم الكامل:</label>
                                    <span class="value">${customer.name}</span>
                                </div>
                                <div class="detail-item">
                                    <label>التصنيف:</label>
                                    <span class="value" style="color: ${customer.segment_color};">● ${customer.segment}</span>
                                </div>
                                <div class="detail-item">
                                    <label>السبب:</label>
                                    <span class="value">${customer.segment_reason}</span>
                                </div>
                                <div class="detail-item">
                                    <label>رقم الهاتف:</label>
                                    <span class="value">${customer.phone || 'غير متوفر'}</span>
                                </div>
                                <div class="detail-item">
                                    <label>المدينة:</label>
                                    <span class="value">${customer.city}</span>
                                </div>
                                <div class="detail-item">
                                    <label>المنطقة:</label>
                                    <span class="value">${customer.area}</span>
                                </div>
                                <div class="detail-item">
                                    <label>نوع العميل:</label>
                                    <span class="value">${customer.type}</span>
                                </div>
                            </div>

                            <div class="detail-group">
                                <h4>💰 إحصائيات المبيعات</h4>
                                <div class="detail-item">
                                    <label>إجمالي GMV:</label>
                                    <span class="value">${customer.total_gmv.toLocaleString('ar')} EGP</span>
                                </div>
                                <div class="detail-item">
                                    <label>عدد الطلبات الفريدة:</label>
                                    <span class="value">${customer.unique_orders}</span>
                                </div>
                                <div class="detail-item">
                                    <label>عدد المنتجات المشتراة:</label>
                                    <span class="value">${customer.item_count}</span>
                                </div>
                                <div class="detail-item">
                                    <label>متوسط قيمة الطلب:</label>
                                    <span class="value">${customer.avg_order_value.toLocaleString('ar')} EGP</span>
                                </div>
                                <div class="detail-item">
                                    <label>عدد المنتجات الفريدة:</label>
                                    <span class="value">${customer.unique_products}</span>
                                </div>
                                <div class="detail-item">
                                    <label>عدد العلامات التجارية:</label>
                                    <span class="value">${customer.unique_brands}</span>
                                </div>
                                <div class="detail-item">
                                    <label>عدد أيام الشراء:</label>
                                    <span class="value">${customer.unique_dates}</span>
                                </div>
                            </div>
                        </div>

                        <div class="expandable-section" onclick="toggleSection(this, event)">
                            <div class="section-header">
                                <span class="section-title">🛍️ المنتجات المطلوبة (${Object.keys(customer.products).length} منتج)</span>
                                <span class="section-toggle">▶</span>
                            </div>
                            <div class="section-content hidden">
                                <div class="products-grid">
                                    ${productsHtml}
                                </div>
                            </div>
                        </div>

                        <div class="expandable-section" onclick="toggleSection(this, event)">
                            <div class="section-header">
                                <span class="section-title">🏷️ العلامات التجارية المفضلة (${Object.keys(customer.brands).length} علامة)</span>
                                <span class="section-toggle">▶</span>
                            </div>
                            <div class="section-content hidden">
                                <div class="brands-grid">
                                    ${brandsHtml}
                                </div>
                            </div>
                        </div>

                        <div class="expandable-section" onclick="toggleSection(this, event)">
                            <div class="section-header">
                                <span class="section-title">📦 سجل الطلبات (${customer.unique_orders} طلب) ${customer.unique_orders > 30 ? '- عرض أول 30' : ''}</span>
                                <span class="section-toggle">▶</span>
                            </div>
                            <div class="section-content hidden">
                                <div class="orders-list">
                                    ${ordersHtml}
                                </div>
                                ${customer.unique_orders > 30 ? `<div style="color: #a1a1aa; margin-top: 15px; font-size: 0.85rem;">... و ${customer.unique_orders - 30} طلب آخر</div>` : ''}
                            </div>
                        </div>
                    </td>
                `;
                tbody.appendChild(detailRow);
            });

            renderPagination();
        }

        function renderPagination() {
            const container = document.getElementById('paginationContainer');
            container.innerHTML = '';

            const totalPages = Math.ceil(filteredData.length / itemsPerPage);

            const prevBtn = document.createElement('button');
            prevBtn.textContent = '← السابق';
            prevBtn.disabled = currentPage === 1;
            prevBtn.onclick = () => {
                if (currentPage > 1) {
                    currentPage--;
                    renderTable();
                }
            };
            container.appendChild(prevBtn);

            const pageInfo = document.createElement('span');
            pageInfo.className = 'page-info';
            pageInfo.textContent = `الصفحة ${currentPage} من ${totalPages}`;
            container.appendChild(pageInfo);

            const nextBtn = document.createElement('button');
            nextBtn.textContent = 'التالي →';
            nextBtn.disabled = currentPage === totalPages;
            nextBtn.onclick = () => {
                if (currentPage < totalPages) {
                    currentPage++;
                    renderTable();
                }
            };
            container.appendChild(nextBtn);
        }

        function toggleDetails(idx) {
            const detailRow = document.getElementById(`detail-${idx}`);
            if (detailRow) {
                detailRow.classList.toggle('hidden');
            }
        }

        function toggleSection(element, event) {
            if (event) {
                event.stopPropagation();
            }
            const section = element.closest('.expandable-section');
            const content = section.querySelector('.section-content');
            section.classList.toggle('expanded');
            content.classList.toggle('hidden');
        }

        function toggleOrderItems(customerIdx, orderIdx, event) {
            if (event) {
                event.stopPropagation();
            }
            const container = document.getElementById(`items-${customerIdx}-${orderIdx}`);
            const arrow = document.getElementById(`arrow-${customerIdx}-${orderIdx}`);
            const orderContainer = container.closest('.order-container');
            
            container.classList.toggle('hidden');
            arrow.style.transform = container.classList.contains('hidden') ? 'rotate(0deg)' : 'rotate(180deg)';
            orderContainer.classList.toggle('expanded');
        }

        // Search functionality
        function setupSearch() {
            const searchInput = document.getElementById('customerSearch');
            if (searchInput) {
                searchInput.addEventListener('keyup', function(e) {
                    const value = e.target.value.toLowerCase();
                    filteredData = customersData.filter(customer => 
                        customer.name.toLowerCase().includes(value) ||
                        String(customer.phone || '').toLowerCase().includes(value) ||
                        customer.city.toLowerCase().includes(value)
                    );
                    currentPage = 1;
                    renderTable();
                });
            }
        }

        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                waitForDataAndRender();
                setupSearch();
            });
        } else {
            waitForDataAndRender();
            setupSearch();
        }
    </script>
</body>
</html>
'''

# Generate external JavaScript data file
js_data = f"""// Dashboard Data - Generated automatically
// DO NOT EDIT THIS FILE MANUALLY

const customersData = {json.dumps(customers_list, ensure_ascii=False)};
const areaGroupsData = {json.dumps(area_groups_sorted, ensure_ascii=False)};
const cityGroupsData = {json.dumps(city_groups_sorted, ensure_ascii=False)};
const segmentsData = {json.dumps(segments_distribution, ensure_ascii=False)};
"""

with open('dashboard_data.js', 'w', encoding='utf-8') as f:
    f.write(js_data)

# Generate HTML file
with open('horeca_modern_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("✅ Comprehensive dashboard generated successfully!")
print(f"📄 Total customers: {total_customers}")
print(f"💰 Total GMV: {total_gmv:,.2f} EGP")
print(f"📦 Total unique orders: {total_unique_orders:,}")
print(f"🎯 Pagination: 25 customers per page")
print(f"📁 Data file: dashboard_data.js (external)")
print(f"🌐 HTML file: horeca_modern_dashboard.html")

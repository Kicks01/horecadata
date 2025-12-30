"""
Fix customer segmentation in dashboard_data.json
Adds segmentation logic that was missing from the enrichment script
"""

import json
import sys

# Ensure UTF-8 output on Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

def classify_customer(customer):
    """
    Classify customers into segments based on their behavior and value
    This matches the logic from generate_comprehensive_dashboard.py
    """
    gmv = customer['total_gmv']
    orders = customer['unique_orders']
    avg_value = customer.get('avg_order_value', 0)
    if avg_value == 0 and orders > 0:
        avg_value = gmv / orders
    unique_dates = customer.get('unique_dates', 0)
    
    # Calculate metrics
    frequency_score = min(unique_dates / 30, 1) * 100 if unique_dates > 0 else 0  # Activity frequency
    value_score = min(gmv / 100000, 1) * 100  # Monetary value
    order_consistency = min(orders / 100, 1) * 100  # Order consistency
    
    # Premium Customer: Top tier by GMV
    if gmv > 1000000:
        return {
            'segment': 'premium',
            'segment_color': '#10b981',
            'segment_reason': 'عميل متميز - قيمة عالية وطلبات متكررة'
        }
    
    # High Value Customer: High GMV
    if gmv > 500000:
        return {
            'segment': 'high_value',
            'segment_color': '#3b82f6',
            'segment_reason': 'عميل عالي القيمة - إنفاق عالي'
        }
    
    # Loyal Customer: Many orders with consistent purchases
    if orders > 200 and frequency_score > 70:
        return {
            'segment': 'loyal',
            'segment_color': '#06b6d4',
            'segment_reason': 'عميل مخلص - منتظم الشراء'
        }
    
    # Growing Customer: Increasing trend (reasonable orders and value)
    if orders > 50 and gmv > 100000 and avg_value > 1000:
        return {
            'segment': 'growing',
            'segment_color': '#8b5cf6',
            'segment_reason': 'عميل نام - نشاط متزايد'
        }
    
    # Potential Customer: Low frequency but good order value
    if avg_value > 500 and orders > 10:
        return {
            'segment': 'potential',
            'segment_color': '#eab308',
            'segment_reason': 'عميل محتمل - له إمكانيات'
        }
    
    # Active Customer: Regular orders
    if orders > 50:
        return {
            'segment': 'active',
            'segment_color': '#8b5cf6',
            'segment_reason': 'عميل نشط - طلبات منتظمة'
        }
    
    # Occasional Customer: Few orders but reasonable value
    if orders > 10 and gmv > 10000:
        return {
            'segment': 'occasional',
            'segment_color': '#a78bfa',
            'segment_reason': 'عميل عارض - طلبات متقطعة'
        }
    
    # Inactive Customer: Very few orders or no recent activity
    if orders <= 5 or unique_dates == 0:
        return {
            'segment': 'inactive',
            'segment_color': '#6b7280',
            'segment_reason': 'عميل غير نشط'
        }
    
    # Lost Customer: Had orders but very low activity
    if orders <= 10 and gmv < 10000:
        return {
            'segment': 'lost',
            'segment_color': '#ef4444',
            'segment_reason': 'عميل مفقود - طلبات قليلة جداً'
        }
    
    # Default
    return {
        'segment': 'regular',
        'segment_color': '#9ca3af',
        'segment_reason': 'عميل عادي'
    }

print("=" * 80)
print("FIXING CUSTOMER SEGMENTATION")
print("=" * 80)
sys.stdout.flush()

# Load dashboard data
print("\n[1/3] Loading dashboard_data.json...")
try:
    with open('dashboard_data.json', 'r', encoding='utf-8') as f:
        dashboard_data = json.load(f)
    print(f"   [OK] Loaded dashboard data with {len(dashboard_data.get('customers', []))} customers")
except Exception as e:
    print(f"   [ERROR] Error loading dashboard_data.json: {e}")
    sys.exit(1)

sys.stdout.flush()

# Fix segmentation for each customer
print("\n[2/3] Calculating segmentation for customers...")
customers = dashboard_data.get('customers', [])
segments_count = {}
segments_gmv = {}

for i, customer in enumerate(customers):
    if (i + 1) % 100 == 0:
        print(f"   Processing customer {i + 1:,} / {len(customers):,}")
        sys.stdout.flush()
    
    # Calculate segmentation
    segmentation = classify_customer(customer)
    
    # Update customer with segmentation
    customer['segment'] = segmentation['segment']
    customer['segment_color'] = segmentation['segment_color']
    customer['segment_reason'] = segmentation['segment_reason']
    
    # Count segments
    seg = segmentation['segment']
    segments_count[seg] = segments_count.get(seg, 0) + 1
    segments_gmv[seg] = segments_gmv.get(seg, 0) + customer['total_gmv']

print(f"   [OK] Processed {len(customers):,} customers")
sys.stdout.flush()

# Update segments distribution
print("\n[3/3] Updating segments distribution...")
segment_colors = {
    'premium': '#10b981',
    'high_value': '#3b82f6',
    'loyal': '#06b6d4',
    'growing': '#8b5cf6',
    'potential': '#eab308',
    'active': '#8b5cf6',
    'occasional': '#a78bfa',
    'inactive': '#6b7280',
    'lost': '#ef4444',
    'regular': '#9ca3af'
}

segment_names = {
    'premium': 'متميز',
    'high_value': 'عالي القيمة',
    'loyal': 'وفي',
    'growing': 'نام',
    'potential': 'محتمل',
    'active': 'نشط',
    'occasional': 'عارض',
    'inactive': 'غير نشط',
    'lost': 'مفقود',
    'regular': 'عادي'
}

segments_distribution = []
for seg in sorted(segments_count.keys()):
    segments_distribution.append({
        'key': seg,
        'name': segment_names.get(seg, seg),
        'color': segment_colors.get(seg, '#9ca3af'),
        'count': segments_count[seg],
        'gmv': segments_gmv[seg]
    })

# Sort by count descending
segments_distribution.sort(key=lambda x: x['count'], reverse=True)

# Update dashboard data
dashboard_data['segments'] = segments_distribution

print(f"   [OK] Created {len(segments_distribution)} segment categories")
for seg in segments_distribution:
    print(f"      - {seg['name']}: {seg['count']} customers, GMV: {seg['gmv']:,.2f}")
sys.stdout.flush()

# Save updated dashboard data
print("\n[4/4] Saving updated dashboard_data.json...")
try:
    with open('dashboard_data.json', 'w', encoding='utf-8') as f:
        json.dump(dashboard_data, f, ensure_ascii=False, indent=2)
    print(f"   [OK] Saved updated dashboard_data.json")
except Exception as e:
    print(f"   [ERROR] Error saving dashboard_data.json: {e}")
    sys.exit(1)

sys.stdout.flush()

print("\n" + "=" * 80)
print("SEGMENTATION FIX COMPLETE!")
print("=" * 80)
print(f"\nSummary:")
print(f"  - Total customers: {len(customers):,}")
print(f"  - Segments created: {len(segments_distribution)}")
print(f"  - All customers now have segmentation data")
sys.stdout.flush()


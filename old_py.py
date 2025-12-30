import csv
import json
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import locale
import calendar

# Set Arabic locale for proper date formatting
try:
    locale.setlocale(locale.LC_ALL, 'ar_EG.UTF-8')
except:
    pass

# Read CSV file (tab-delimited)
data = []
with open('2025 horeca.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        data.append(row)

print(f"Total rows: {len(data)}")
print("Processing data...")

# Date parsing function
def parse_date(date_str):
    """Parse date string to datetime object"""
    if not date_str or date_str.strip() == '':
        return None
    
    # Try different date formats
    formats = ['%m/%d/%Y', '%d/%m/%Y', '%Y-%m-%d', '%m-%d-%Y', '%d-%m-%Y']
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except:
            continue
    return None

# Extract area and city from address
def extract_area_city_from_address(address, customer_id):
    """Extract area and city from address string"""
    if not address or address.strip() == '':
        return 'غير محدد', 'غير محدد'
    
    address = address.strip()
    
    # Common patterns: address ends with ", Area, City" or ", City Governorate"
    # Split by comma and get last parts
    parts = [p.strip() for p in address.split(',') if p.strip()]
    
    if len(parts) >= 2:
        # Last part is usually city/governorate
        last_part = parts[-1]
        second_last = parts[-2] if len(parts) >= 2 else ''
        
        # Remove numbers and postal codes
        city = last_part
        # Remove postal codes (numbers at the end)
        city = ' '.join([w for w in city.split() if not w.isdigit()])
        
        # Common governorate patterns
        if 'Governorate' in city:
            city = city.replace('Governorate', '').strip()
        if 'Cairo' in city:
            city = 'القاهرة'
        elif 'Giza' in city:
            city = 'الجيزة'
        elif 'Alexandria' in city:
            city = 'الإسكندرية'
        elif 'Al-Qalyubia' in city or 'Qalyubia' in city:
            city = 'القليوبية'
        elif 'Al-Sharqia' in city or 'Sharqia' in city:
            city = 'الشرقية'
        elif 'Suez' in city:
            city = 'السويس'
        elif 'Ismailia' in city:
            city = 'الإسماعيلية'
        elif 'Menofia' in city:
            city = 'المنوفية'
        elif 'Gharbia' in city:
            city = 'الغربية'
        elif 'Dakahlia' in city:
            city = 'الدقهلية'
        elif 'Beheira' in city:
            city = 'البحيرة'
        elif 'Qena' in city:
            city = 'قنا'
        elif 'Faiyum' in city:
            city = 'الفيوم'
        elif 'Beni Suef' in city:
            city = 'بني سويف'
        
        # Area is usually the second-to-last part or extracted from Arabic text
        area = second_last if second_last else 'غير محدد'
        
        # Try to extract Arabic area name from the address
        # Look for Arabic text before the last comma
        arabic_parts = []
        for part in parts[:-1]:
            # Check if part contains Arabic characters
            if any('\u0600' <= char <= '\u06FF' for char in part):
                arabic_parts.append(part)
        
        if arabic_parts:
            # Use the last Arabic part as area
            area = arabic_parts[-1]
        
        # Clean area name
        area = area.replace('،', '').replace(',', '').strip()
        if not area or area == '':
            area = 'غير محدد'
        
        return area, city
    
    # If no clear pattern, try to extract from Arabic text
    # Look for common area indicators
    arabic_text = ' '.join([p for p in parts if any('\u0600' <= char <= '\u06FF' for char in p)])
    
    if arabic_text:
        # Try to find area name (usually before last comma or in middle)
        area = arabic_text.split('،')[-1].strip() if '،' in arabic_text else arabic_text.split(',')[-1].strip()
        city = 'غير محدد'
        return area, city
    
    return 'غير محدد', 'غير محدد'

# Build customer ID to address mapping first
print("Building customer address mapping...")
customer_addresses = {}  # id -> address
for row in data:
    customer_id = row.get('id', '').strip()
    name = row.get('name', '').strip()
    if customer_id and name and name != 'Location' and customer_id not in customer_addresses:
        customer_addresses[customer_id] = name

# Calculate total revenue
total_revenue = sum(float(row.get('price_gross', 0) or 0) * float(row.get('amount', 0) or 0) for row in data)
total_quantity = sum(float(row.get('amount', 0) or 0) for row in data)

# Build direct reference structures
customers = {}  # phone -> customer info
areas = defaultdict(lambda: {'customers': set(), 'revenue': 0, 'quantity': 0, 'orders': set()})
cities = defaultdict(lambda: {'areas': set(), 'customers': set(), 'revenue': 0, 'quantity': 0, 'orders': set()})
products = defaultdict(lambda: {'customers': set(), 'revenue': 0, 'quantity': 0, 'orders': set(), 'details': []})
brands = defaultdict(lambda: {'products': set(), 'customers': set(), 'revenue': 0, 'quantity': 0})
categories = defaultdict(lambda: {'products': set(), 'customers': set(), 'revenue': 0, 'quantity': 0})

print("Building reference structures...")
for idx, row in enumerate(data):
    if (idx + 1) % 10000 == 0:
        print(f"Processed {idx + 1:,} rows...")
    
    order_id = row.get('order_id', '')
    amount = float(row.get('amount', 0) or 0)
    price = float(row.get('price_gross', 0) or 0)
    revenue = amount * price
    
    phone = row.get('phone', '').strip()
    name = row.get('name', 'غير محدد').strip()
    customer_id = row.get('id', '').strip()
    
    # Get area and city from CSV columns first
    area = row.get('area', 'غير محدد').strip()
    city = row.get('city', 'غير محدد').strip()
    
    # If area or city is missing, try to extract from address
    if (area == 'غير محدد' or area == '' or city == 'غير محدد' or city == '') and customer_id in customer_addresses:
        address = customer_addresses[customer_id]
        extracted_area, extracted_city = extract_area_city_from_address(address, customer_id)
        if area == 'غير محدد' or area == '':
            area = extracted_area
        if city == 'غير محدد' or city == '':
            city = extracted_city
    product = row.get('product', 'غير محدد').strip()
    brand = row.get('brand', 'غير محدد').strip()
    category = row.get('category', 'غير محدد').strip()
    type_val = row.get('Type', 'غير محدد').strip()
    date_str = row.get('date', '')
    
    # Build customer reference
    if phone:
        if phone not in customers:
            customers[phone] = {
                'name': name,
                'phone': phone,
                'area': area,
                'city': city,
                'type': type_val,
                'revenue': 0,
                'quantity': 0,
                'orders': set(),
                'products': defaultdict(lambda: {'revenue': 0, 'quantity': 0, 'orders': set()}),
                'details': []
            }
        
        customers[phone]['revenue'] += revenue
        customers[phone]['quantity'] += amount
        customers[phone]['orders'].add(order_id)
        customers[phone]['products'][product]['revenue'] += revenue
        customers[phone]['products'][product]['quantity'] += amount
        customers[phone]['products'][product]['orders'].add(order_id)
        
        # Limit details to prevent memory issues
        if len(customers[phone]['details']) < 50:
            customers[phone]['details'].append({
                'order_id': order_id,
                'date': date_str,
                'product': product,
                'brand': brand,
                'category': category,
                'amount': amount,
                'price': price,
                'revenue': revenue
            })
    
    # Build area reference
    areas[area]['customers'].add(phone if phone else f"no_phone_{order_id}")
    areas[area]['revenue'] += revenue
    areas[area]['quantity'] += amount
    areas[area]['orders'].add(order_id)
    
    # Build city reference
    cities[city]['areas'].add(area)
    cities[city]['customers'].add(phone if phone else f"no_phone_{order_id}")
    cities[city]['revenue'] += revenue
    cities[city]['quantity'] += amount
    cities[city]['orders'].add(order_id)
    
    # Build product reference
    products[product]['customers'].add(phone if phone else f"no_phone_{order_id}")
    products[product]['revenue'] += revenue
    products[product]['quantity'] += amount
    products[product]['orders'].add(order_id)
    # Limit product details to prevent memory issues
    if len(products[product]['details']) < 20:
        products[product]['details'].append({
            'order_id': order_id,
            'date': date_str,
            'customer_phone': phone,
            'customer_name': name,
            'area': area,
            'city': city,
            'brand': brand,
            'category': category,
            'amount': amount,
            'price': price,
            'revenue': revenue
        })
    
    # Build brand reference
    brands[brand]['products'].add(product)
    brands[brand]['customers'].add(phone if phone else f"no_phone_{order_id}")
    brands[brand]['revenue'] += revenue
    brands[brand]['quantity'] += amount
    
    # Build category reference
    categories[category]['products'].add(product)
    categories[category]['customers'].add(phone if phone else f"no_phone_{order_id}")
    categories[category]['revenue'] += revenue
    categories[category]['quantity'] += amount

print("Finalizing structures...")
# Convert sets to counts
for area in areas:
    areas[area]['customer_count'] = len(areas[area]['customers'])
    areas[area]['order_count'] = len(areas[area]['orders'])
    del areas[area]['customers']
    del areas[area]['orders']

for city in cities:
    cities[city]['area_count'] = len(cities[city]['areas'])
    cities[city]['customer_count'] = len(cities[city]['customers'])
    cities[city]['order_count'] = len(cities[city]['orders'])
    del cities[city]['areas']
    del cities[city]['customers']
    del cities[city]['orders']

for product in products:
    products[product]['customer_count'] = len(products[product]['customers'])
    products[product]['order_count'] = len(products[product]['orders'])
    del products[product]['customers']
    del products[product]['orders']

for brand in brands:
    brands[brand]['product_count'] = len(brands[brand]['products'])
    brands[brand]['customer_count'] = len(brands[brand]['customers'])
    del brands[brand]['products']
    del brands[brand]['customers']

for category in categories:
    categories[category]['product_count'] = len(categories[category]['products'])
    categories[category]['customer_count'] = len(categories[category]['customers'])
    del categories[category]['products']
    del categories[category]['customers']

for phone in customers:
    customers[phone]['order_count'] = len(customers[phone]['orders'])
    del customers[phone]['orders']
    # Convert products dict to sorted list
    customers[phone]['products'] = sorted(
        customers[phone]['products'].items(),
        key=lambda x: x[1]['revenue'],
        reverse=True
    )

# Sort all references
sorted_customers = sorted(
    customers.items(),
    key=lambda x: x[1]['revenue'],
    reverse=True
)

sorted_areas = sorted(
    areas.items(),
    key=lambda x: x[1]['revenue'],
    reverse=True
)

sorted_cities = sorted(
    cities.items(),
    key=lambda x: x[1]['revenue'],
    reverse=True
)

sorted_products = sorted(
    products.items(),
    key=lambda x: x[1]['revenue'],
    reverse=True
)

sorted_brands = sorted(
    brands.items(),
    key=lambda x: x[1]['revenue'],
    reverse=True
)

sorted_categories = sorted(
    categories.items(),
    key=lambda x: x[1]['revenue'],
    reverse=True
)

print("Generating HTML...")
# Write HTML directly to file instead of building huge string
with open('horeca_analysis.html', 'w', encoding='utf-8') as f:
    # Write header
    f.write(f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مرجع بيانات Horeca 2025 - دليل مباشر للعملاء والمناطق والمنتجات</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
            min-height: 100vh;
            padding: 20px;
            direction: rtl;
        }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            border-radius: 10px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .header h1 {{
            color: #1e40af;
            font-size: 2.2em;
            margin-bottom: 10px;
        }}
        
        .header .subtitle {{
            color: #666;
            font-size: 1.1em;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        
        .stat-card .label {{
            color: #666;
            font-size: 0.9em;
            margin-bottom: 8px;
        }}
        
        .stat-card .value {{
            color: #1e40af;
            font-size: 1.8em;
            font-weight: bold;
        }}
        
        .section {{
            background: white;
            border-radius: 10px;
            padding: 25px;
            margin-bottom: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .section-title {{
            color: #1e40af;
            font-size: 1.6em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e5e7eb;
        }}
        
        .table-container {{
            overflow-x: auto;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.95em;
        }}
        
        thead {{
            background: #f3f4f6;
        }}
        
        th {{
            padding: 12px;
            text-align: right;
            color: #1e40af;
            font-weight: 600;
            border-bottom: 2px solid #e5e7eb;
            position: sticky;
            top: 0;
            background: #f3f4f6;
        }}
        
        td {{
            padding: 10px 12px;
            color: #374151;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        tr:hover {{
            background: #f9fafb;
        }}
        
        .number {{
            text-align: left;
            font-family: 'Courier New', monospace;
        }}
        
        .customer-row {{
            cursor: pointer;
        }}
        
        .customer-details {{
            display: none;
            background: #f9fafb;
            padding: 20px;
            margin: 10px 0;
            border-radius: 8px;
            border-right: 4px solid #3b82f6;
        }}
        
        .customer-details.active {{
            display: block;
        }}
        
        .customer-details h4 {{
            color: #1e40af;
            margin-bottom: 15px;
            font-size: 1.2em;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .info-item {{
            background: white;
            padding: 12px;
            border-radius: 6px;
        }}
        
        .info-item label {{
            color: #3b82f6;
            font-weight: 600;
            display: block;
            margin-bottom: 5px;
            font-size: 0.9em;
        }}
        
        .info-item value {{
            color: #1e3a8a;
            font-size: 1.1em;
        }}
        
        .search-box {{
            width: 100%;
            padding: 12px;
            border: 2px solid #e5e7eb;
            border-radius: 8px;
            font-size: 1em;
            margin-bottom: 20px;
            direction: rtl;
        }}
        
        .search-box:focus {{
            outline: none;
            border-color: #3b82f6;
        }}
        
        .highlight {{
            background: #fef3c7;
            padding: 2px 4px;
            border-radius: 3px;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.5em;
            }}
            
            table {{
                font-size: 0.85em;
            }}
            
            th, td {{
                padding: 8px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 مرجع بيانات Horeca 2025</h1>
            <p class="subtitle">دليل مباشر شامل للعملاء والمناطق والمنتجات - كل المعلومات في مكان واحد</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">إجمالي الإيرادات</div>
                <div class="value">{total_revenue:,.0f} ج.م</div>
            </div>
            <div class="stat-card">
                <div class="label">إجمالي الكمية</div>
                <div class="value">{total_quantity:,.0f} وحدة</div>
            </div>
            <div class="stat-card">
                <div class="label">عدد العملاء</div>
                <div class="value">{len(customers):,} عميل</div>
            </div>
            <div class="stat-card">
                <div class="label">عدد المناطق</div>
                <div class="value">{len(areas):,} منطقة</div>
            </div>
            <div class="stat-card">
                <div class="label">عدد المدن</div>
                <div class="value">{len(cities):,} مدينة</div>
            </div>
            <div class="stat-card">
                <div class="label">عدد المنتجات</div>
                <div class="value">{len(products):,} منتج</div>
            </div>
        </div>
""")

    # Generate Customers Section - Complete list
    f.write(f"""
        <div class="section">
            <h2 class="section-title">👥 قائمة العملاء الكاملة ({len(customers):,} عميل)</h2>
            <input type="text" class="search-box" id="customerSearch" placeholder="🔍 ابحث عن عميل بالاسم أو رقم الهاتف أو المنطقة..." onkeyup="filterTable('customerSearch', 'customersTable')">
            <div class="table-container">
                <table id="customersTable">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>اسم العميل</th>
                            <th>رقم الهاتف</th>
                            <th>المنطقة</th>
                            <th>المدينة</th>
                            <th>النوع</th>
                            <th>الإيرادات (ج.م)</th>
                            <th>الكمية</th>
                            <th>عدد الطلبات</th>
                        </tr>
                    </thead>
                    <tbody>
""")

    customer_id = 0
    for idx, (phone, customer) in enumerate(sorted_customers, 1):
        customer_id += 1
        f.write(f"""
                        <tr class="customer-row" onclick="toggleCustomer({customer_id})">
                            <td class="number">{idx}</td>
                            <td><strong>{customer['name']}</strong></td>
                            <td>{phone}</td>
                            <td>{customer['area']}</td>
                            <td>{customer['city']}</td>
                            <td>{customer['type']}</td>
                            <td class="number">{customer['revenue']:,.2f}</td>
                            <td class="number">{customer['quantity']:,.0f}</td>
                            <td class="number">{customer['order_count']:,}</td>
                        </tr>
""")
    
        # Customer details
        details_html = f"""
            <tr id="customer-{customer_id}" class="customer-details">
                <td colspan="9">
                    <div style="padding: 20px;">
                        <h4>تفاصيل العميل: {customer['name']}</h4>
                        <div class="info-grid">
                            <div class="info-item">
                                <label>رقم الهاتف:</label>
                                <value>{phone}</value>
                            </div>
                            <div class="info-item">
                                <label>المنطقة:</label>
                                <value>{customer['area']}</value>
                            </div>
                            <div class="info-item">
                                <label>المدينة:</label>
                                <value>{customer['city']}</value>
                            </div>
                            <div class="info-item">
                                <label>النوع:</label>
                                <value>{customer['type']}</value>
                            </div>
                            <div class="info-item">
                                <label>إجمالي الإيرادات:</label>
                                <value>{customer['revenue']:,.2f} ج.م</value>
                            </div>
                            <div class="info-item">
                                <label>إجمالي الكمية:</label>
                                <value>{customer['quantity']:,.0f} وحدة</value>
                            </div>
                            <div class="info-item">
                                <label>عدد الطلبات:</label>
                                <value>{customer['order_count']:,} طلب</value>
                            </div>
                        </div>
                        <h4 style="margin-top: 20px; margin-bottom: 10px;">المنتجات المشتراة ({len(customer['products'])} منتج):</h4>
                        <table style="margin-top: 10px;">
                            <thead>
                                <tr>
                                    <th>المنتج</th>
                                    <th>الإيرادات (ج.م)</th>
                                    <th>الكمية</th>
                                </tr>
                            </thead>
                            <tbody>
    """
    
        for product_name, product_stats in customer['products'][:20]:  # Top 20 products
            details_html += f"""
                                <tr>
                                    <td>{product_name}</td>
                                    <td class="number">{product_stats['revenue']:,.2f}</td>
                                    <td class="number">{product_stats['quantity']:,.0f}</td>
                                </tr>
        """
    
        details_html += """
                            </tbody>
                        </table>
                        <h4 style="margin-top: 20px; margin-bottom: 10px;">تفاصيل الطلبات ({count} عنصر):</h4>
                        <table style="margin-top: 10px;">
                            <thead>
                                <tr>
                                    <th>رقم الطلب</th>
                                    <th>التاريخ</th>
                                    <th>المنتج</th>
                                    <th>الماركة</th>
                                    <th>الفئة</th>
                                    <th>الكمية</th>
                                    <th>السعر</th>
                                    <th>الإيراد</th>
                                </tr>
                            </thead>
                            <tbody>
    """
    
        for detail in customer['details']:  # Already limited to 50 items
            details_html += f"""
                                <tr>
                                    <td>{detail.get('order_id', '')}</td>
                                    <td>{detail.get('date', '')}</td>
                                    <td>{detail.get('product', '')}</td>
                                    <td>{detail.get('brand', '')}</td>
                                    <td>{detail.get('category', '')}</td>
                                    <td class="number">{detail.get('amount', 0):,.0f}</td>
                                    <td class="number">{detail.get('price', 0):,.2f}</td>
                                    <td class="number">{detail.get('revenue', 0):,.2f}</td>
                                </tr>
        """
    
        details_html = details_html.replace('{count}', str(len(customer['details'])))
        details_html += """
                            </tbody>
                        </table>
                    </div>
                </td>
            </tr>
    """
        
        f.write(details_html)

    f.write("""
                    </tbody>
                </table>
            </div>
        </div>
""")

    # Generate Areas Section
    f.write(f"""
        <div class="section">
            <h2 class="section-title">📍 قائمة المناطق الكاملة ({len(areas):,} منطقة)</h2>
            <input type="text" class="search-box" id="areaSearch" placeholder="🔍 ابحث عن منطقة..." onkeyup="filterTable('areaSearch', 'areasTable')">
            <div class="table-container">
                <table id="areasTable">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>اسم المنطقة</th>
                            <th>عدد العملاء</th>
                            <th>الإيرادات (ج.م)</th>
                            <th>الكمية</th>
                            <th>عدد الطلبات</th>
                        </tr>
                    </thead>
                    <tbody>
""")

    for idx, (area_name, area_data) in enumerate(sorted_areas, 1):
        f.write(f"""
                        <tr>
                            <td class="number">{idx}</td>
                            <td><strong>{area_name}</strong></td>
                            <td class="number">{area_data['customer_count']:,}</td>
                            <td class="number">{area_data['revenue']:,.2f}</td>
                            <td class="number">{area_data['quantity']:,.0f}</td>
                            <td class="number">{area_data['order_count']:,}</td>
                        </tr>
        """)

    f.write("""
                    </tbody>
                </table>
            </div>
        </div>
""")

    # Generate Cities Section
    f.write(f"""
        <div class="section">
            <h2 class="section-title">🏙️ قائمة المدن الكاملة ({len(cities):,} مدينة)</h2>
            <input type="text" class="search-box" id="citySearch" placeholder="🔍 ابحث عن مدينة..." onkeyup="filterTable('citySearch', 'citiesTable')">
            <div class="table-container">
                <table id="citiesTable">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>اسم المدينة</th>
                            <th>عدد المناطق</th>
                            <th>عدد العملاء</th>
                            <th>الإيرادات (ج.م)</th>
                            <th>الكمية</th>
                            <th>عدد الطلبات</th>
                        </tr>
                    </thead>
                    <tbody>
""")

    for idx, (city_name, city_data) in enumerate(sorted_cities, 1):
        f.write(f"""
                        <tr>
                            <td class="number">{idx}</td>
                            <td><strong>{city_name}</strong></td>
                            <td class="number">{city_data['area_count']:,}</td>
                            <td class="number">{city_data['customer_count']:,}</td>
                            <td class="number">{city_data['revenue']:,.2f}</td>
                            <td class="number">{city_data['quantity']:,.0f}</td>
                            <td class="number">{city_data['order_count']:,}</td>
                        </tr>
        """)

    f.write("""
                    </tbody>
                </table>
            </div>
        </div>
""")

    # Generate Products Section
    f.write(f"""
        <div class="section">
            <h2 class="section-title">🛍️ قائمة المنتجات الكاملة ({len(products):,} منتج)</h2>
            <input type="text" class="search-box" id="productSearch" placeholder="🔍 ابحث عن منتج..." onkeyup="filterTable('productSearch', 'productsTable')">
            <div class="table-container">
                <table id="productsTable">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>اسم المنتج</th>
                            <th>عدد العملاء</th>
                            <th>الإيرادات (ج.م)</th>
                            <th>الكمية</th>
                            <th>عدد الطلبات</th>
                        </tr>
                    </thead>
                    <tbody>
""")

    for idx, (product_name, product_data) in enumerate(sorted_products, 1):
        f.write(f"""
                        <tr>
                            <td class="number">{idx}</td>
                            <td><strong>{product_name}</strong></td>
                            <td class="number">{product_data['customer_count']:,}</td>
                            <td class="number">{product_data['revenue']:,.2f}</td>
                            <td class="number">{product_data['quantity']:,.0f}</td>
                            <td class="number">{product_data['order_count']:,}</td>
                        </tr>
        """)

    f.write("""
                    </tbody>
                </table>
            </div>
        </div>
""")

    # Generate Brands Section
    f.write(f"""
        <div class="section">
            <h2 class="section-title">🏅 قائمة الماركات ({len(brands):,} ماركة)</h2>
            <input type="text" class="search-box" id="brandSearch" placeholder="🔍 ابحث عن ماركة..." onkeyup="filterTable('brandSearch', 'brandsTable')">
            <div class="table-container">
                <table id="brandsTable">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>اسم الماركة</th>
                            <th>عدد المنتجات</th>
                            <th>عدد العملاء</th>
                            <th>الإيرادات (ج.م)</th>
                            <th>الكمية</th>
                        </tr>
                    </thead>
                    <tbody>
""")

    for idx, (brand_name, brand_data) in enumerate(sorted_brands, 1):
        f.write(f"""
                        <tr>
                            <td class="number">{idx}</td>
                            <td><strong>{brand_name}</strong></td>
                            <td class="number">{brand_data['product_count']:,}</td>
                            <td class="number">{brand_data['customer_count']:,}</td>
                            <td class="number">{brand_data['revenue']:,.2f}</td>
                            <td class="number">{brand_data['quantity']:,.0f}</td>
                        </tr>
        """)

    f.write("""
                    </tbody>
                </table>
            </div>
        </div>
""")

    # Generate Categories Section
    f.write(f"""
        <div class="section">
            <h2 class="section-title">📦 قائمة الفئات ({len(categories):,} فئة)</h2>
            <input type="text" class="search-box" id="categorySearch" placeholder="🔍 ابحث عن فئة..." onkeyup="filterTable('categorySearch', 'categoriesTable')">
            <div class="table-container">
                <table id="categoriesTable">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>اسم الفئة</th>
                            <th>عدد المنتجات</th>
                            <th>عدد العملاء</th>
                            <th>الإيرادات (ج.م)</th>
                            <th>الكمية</th>
                        </tr>
                    </thead>
                    <tbody>
""")

    for idx, (category_name, category_data) in enumerate(sorted_categories, 1):
        f.write(f"""
                        <tr>
                            <td class="number">{idx}</td>
                            <td><strong>{category_name}</strong></td>
                            <td class="number">{category_data['product_count']:,}</td>
                            <td class="number">{category_data['customer_count']:,}</td>
                            <td class="number">{category_data['revenue']:,.2f}</td>
                            <td class="number">{category_data['quantity']:,.0f}</td>
                        </tr>
        """)

    f.write("""
                    </tbody>
                </table>
            </div>
        </div>
""")

    # Add JavaScript for search and toggle
    f.write("""
        <script>
            function filterTable(searchId, tableId) {
                const input = document.getElementById(searchId);
                const filter = input.value.toUpperCase();
                const table = document.getElementById(tableId);
                const tr = table.getElementsByTagName("tr");
                
                for (let i = 1; i < tr.length; i++) {
                    const td = tr[i].getElementsByTagName("td");
                    let txtValue = "";
                    for (let j = 0; j < td.length; j++) {
                        if (td[j]) {
                            txtValue += td[j].textContent || td[j].innerText;
                        }
                    }
                    if (txtValue.toUpperCase().indexOf(filter) > -1) {
                        tr[i].style.display = "";
                    } else {
                        tr[i].style.display = "none";
                    }
                }
            }
            
            function toggleCustomer(id) {
                const details = document.getElementById('customer-' + id);
                if (details) {
                    details.classList.toggle('active');
                }
            }
        </script>
    </div>
</body>
</html>
""")

print("HTML file generated successfully!")
print(f"Total revenue: {total_revenue:,.2f}")
print(f"Total quantity: {total_quantity:,.0f}")
print(f"Total rows: {len(data)}")
print(f"Total customers: {len(customers)}")
print(f"Total areas: {len(areas)}")
print(f"Total cities: {len(cities)}")
print(f"Total products: {len(products)}")

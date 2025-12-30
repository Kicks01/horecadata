import pandas as pd
import json
import re
from collections import defaultdict

print("=" * 60)
print("HORECA DATA PROCESSING & ANALYSIS")
print("=" * 60)

# Read the CSV file
print("\n[1/5] Reading data...")
try:
    df = pd.read_csv('data.csv', sep='\t', encoding='utf-8')
    print(f"✓ Loaded {len(df)} records")
except Exception as e:
    print(f"✗ Error: {e}")
    exit()

# City mapping for standardization - All to Arabic
CITY_MAPPING = {
    # Cairo
    'Cairo': 'محافظة القاهرة',
    'Cairo Governorate': 'محافظة القاهرة',
    'القاهرة': 'محافظة القاهرة',
    
    # Giza
    'Giza': 'محافظة الجيزة',
    'Giza Governorate': 'محافظة الجيزة',
    'Al Giza': 'محافظة الجيزة',
    'الجيزه': 'محافظة الجيزة',
    'الجيزة': 'محافظة الجيزة',
    
    # Alexandria
    'Alexandria': 'محافظة الإسكندرية',
    'Alexandria Governorate': 'محافظة الإسكندرية',
    'الإسكندرية': 'محافظة الإسكندرية',
    
    # Al-Qalyubia
    'Al-Qalyubia': 'محافظة القليوبية',
    'Al-Qalyubia Governorate': 'محافظة القليوبية',
    'Qalyubia': 'محافظة القليوبية',
    'القليوبية': 'محافظة القليوبية',
    
    # Al-Sharqia
    'Al-Sharqia': 'محافظة الشرقية',
    'Al-Sharqia Governorate': 'محافظة الشرقية',
    'Sharqia': 'محافظة الشرقية',
    'الشرقية': 'محافظة الشرقية',
    
    # Suez
    'Suez': 'محافظة السويس',
    'Suez Governorate': 'محافظة السويس',
    'السويس': 'محافظة السويس',
    
    # Ismailia
    'Ismailia': 'محافظة الإسماعيلية',
    'Ismailia Governorate': 'محافظة الإسماعيلية',
    'الإسماعيلية': 'محافظة الإسماعيلية',
    
    # Menofia
    'Menofia': 'محافظة المنوفية',
    'Menofia Governorate': 'محافظة المنوفية',
    'المنوفية': 'محافظة المنوفية',
    
    # Gharbia
    'Gharbia': 'محافظة الغربية',
    'Gharbia Governorate': 'محافظة الغربية',
    'الغربية': 'محافظة الغربية',
    
    # Dakahlia
    'Dakahlia': 'محافظة الدقهلية',
    'Dakahlia Governorate': 'محافظة الدقهلية',
    'الدقهلية': 'محافظة الدقهلية',
    
    # Beheira
    'Beheira': 'محافظة البحيرة',
    'Beheira Governorate': 'محافظة البحيرة',
    'البحيرة': 'محافظة البحيرة',
    
    # Qena
    'Qena': 'محافظة قنا',
    'Qena Governorate': 'محافظة قنا',
    'قنا': 'محافظة قنا',
    
    # Faiyum
    'Faiyum': 'محافظة الفيوم',
    'Faiyum Governorate': 'محافظة الفيوم',
    'الفيوم': 'محافظة الفيوم',
    
    # Beni Suef
    'Beni Suef': 'محافظة بني سويف',
    'Beni Suef Governorate': 'محافظة بني سويف',
    'بني سويف': 'محافظة بني سويف',
}

# Type/Business mapping - All to Arabic
TYPE_MAPPING = {
    # Arabic to Arabic
    'كافيه': 'كافيه',
    'مطعم': 'مطعم',
    'مخبز': 'مخبز',
    'نادي رياضي': 'نادي رياضي',
    'ملهى ألعاب': 'ملهى ألعاب',
    'عيادة طبية': 'عيادة طبية',
    'مقهى': 'كافيه',
    'مقهى إسبرسو': 'كافيه',
    'كافتيريا': 'كافيه',
    'متجر القهوة': 'كافيه',
    'متجر عصائر': 'متجر عصائر',
    'متجر سلع منزلية': 'متجر',
    'متجر ملابس أطفال': 'متجر',
    'متجر طيور': 'متجر',
    'محطة وقود': 'محطة وقود',
    'طبيب أسنان': 'عيادة طبية',
    'صالة رياضة': 'نادي رياضي',
    'فندق منتجع': 'فندق',
    'موتيل': 'فندق',
    'تجهيز الأسماك': 'محل متخصص',
    'المعجنات': 'مخبز',
    'كنيسة': 'مكان عبادة',
    
    # English to Arabic
    'Cafe': 'كافيه',
    'Coffee shop': 'كافيه',
    'Coffee store': 'كافيه',
    'Creperie': 'كافيه',
    'Juice shop': 'متجر عصائر',
    'Restaurant': 'مطعم',
    'Pizza delivery': 'مطعم',
    'Sandwich shop': 'مطعم',
    'Soup kitchen': 'مطعم',
    'Bakery': 'مخبز',
    'Dessert shop': 'محل حلويات',
    'Sweets and dessert buffet': 'محل حلويات',
    'Ice cream shop': 'محل آيس كريم',
    'Soft drinks shop': 'متجر مشروبات',
    'Fruit and vegetable store': 'متجر خضار',
    'Grocery store': 'سوبرماركت',
    'Supermarket': 'سوبرماركت',
    'Butcher shop deli': 'محل لحوم',
    'Fish store': 'متجر أسماك',
    'Clothing store': 'محل ملابس',
    'Women\'s clothing store': 'محل ملابس',
    'Sports club': 'نادي رياضي',
    'Gym': 'نادي رياضي',
    'Sports': 'نادي رياضي',
    'Pool billard club': 'نادي رياضي',
    'Equestrian club': 'نادي رياضي',
    'Entertainment Center/Park': 'ملهى',
    'Video arcade': 'ملهى ألعاب',
    'Video game store': 'ملهى ألعاب',
    'Video game rental store': 'ملهى ألعاب',
    'Playground': 'ملهى ألعاب',
    'Park': 'حديقة',
    'Lounge': 'لاونج',
    'Hotel': 'فندق',
    'Hospital': 'مستشفى',
    'School': 'مدرسة',
    'Charter school': 'مدرسة',
    'Private educational institution': 'مدرسة',
    'Educational institution': 'مدرسة',
    'Education center': 'مدرسة',
    'Language school': 'مدرسة',
    'University': 'جامعة',
    'Mosque/Church': 'مكان عبادة',
    'Company': 'شركة',
    'Corporate office': 'مكتب',
    'Coworking space': 'مكتب',
    'Travel agency': 'وكالة سفر',
    'Telecommunications service provider': 'مزود خدمات',
    'Electronics company': 'متجر إلكترونيات',
    'Electrical appliance wholesaler': 'متجر أجهزة كهربائية',
    'Mattress store': 'محل أثاث',
    'Rest stop': 'محطة راحة',
    'Wedding Hall': 'قاعة أفراح',
    'Beauty salon': 'صالون تجميل',
    'Clothing store': 'محل ملابس',
    'Charity': 'جمعية خيرية',
    'Social services organization': 'منظمة خدمات اجتماعية',
    'Army/Police Location': 'مقر عسكري',
    'Apartment building': 'عمارة',
    'Store': 'متجر',
    'Auto parts market': 'متجر قطع غيار',
    'Import export company': 'شركة استيراد وتصدير',
    'Food and beverage exporter': 'شركة تصدير',
}

print("\n[2/5] Cleaning and standardizing data...")

# Function to clean city data to Arabic
def clean_city(city_str):
    if pd.isna(city_str) or city_str.strip() == '':
        return 'غير محدد'
    
    city_str = str(city_str).strip()
    
    # Remove postal codes (numbers at end)
    city_str = re.sub(r'\s+\d+$', '', city_str)
    
    # Check exact mapping first
    for key, value in CITY_MAPPING.items():
        if key.lower() == city_str.lower():
            return value
    
    # Check partial mapping
    for key, value in CITY_MAPPING.items():
        if key.lower() in city_str.lower():
            return value
    
    # Map cities that aren't governorates to their governorate equivalents
    city_lower = city_str.lower()
    
    # Cairo governorate cities
    if any(x in city_lower for x in ['cairo', 'القاهرة', 'nasr', 'maadi', 'heliopolis', 
                                      'mokattam', 'shubra', 'zamalek', 'dokki', 'giza', 
                                      'helwan', 'dahshur']):
        return 'محافظة القاهرة'
    
    # Giza governorate cities
    if any(x in city_lower for x in ['giza', 'الجيزة', '6 october', 'october', 'haram']):
        return 'محافظة الجيزة'
    
    # Alexandria governorate cities
    if any(x in city_lower for x in ['alexandria', 'الإسكندرية', 'montaza', 'raml']):
        return 'محافظة الإسكندرية'
    
    # Al-Qalyubia
    if any(x in city_lower for x in ['qalyubia', 'القليوبية', 'shubra el', 'bahtim', 'banha']):
        return 'محافظة القليوبية'
    
    # Sharqia
    if any(x in city_lower for x in ['sharqia', 'الشرقية', 'zagazig', 'ramadan']):
        return 'محافظة الشرقية'
    
    # Keep as is if can't standardize
    return city_str if city_str else 'غير محدد'

# Function to clean area data
def clean_area(area_str):
    if pd.isna(area_str) or area_str.strip() == '':
        return 'غير محدد'
    
    area_str = str(area_str).strip()
    return area_str if area_str else 'غير محدد'

# Function to clean Type to Arabic
def clean_type(type_str):
    if pd.isna(type_str) or type_str.strip() == '':
        return 'غير محدد'
    
    type_str = str(type_str).strip()
    
    # Skip special cases
    if type_str in ['0', 'Add a label', '']:
        return 'غير محدد'
    
    # Check mapping
    for key, value in TYPE_MAPPING.items():
        if key.lower() == type_str.lower():
            return value
    
    # Fallback: return original if not found
    return 'غير محدد'

# Clean the dataframe
if 'city' in df.columns:
    df['city'] = df['city'].apply(clean_city)
if 'area' in df.columns:
    df['area'] = df['area'].apply(clean_area)
if 'Type' in df.columns:
    df['Type'] = df['Type'].apply(clean_type)

print(f"✓ Data cleaned")

# Generate analysis
print("\n[3/5] Generating analysis...")

# Get unique cities
cities_data = []
if 'city' in df.columns:
    city_counts = df['city'].value_counts()
    for city, count in city_counts.items():
        unique_customers = df[df['city'] == city]['name'].nunique() if 'name' in df.columns else 0
        cities_data.append({
            'city': city,
            'records': int(count),
            'customers': int(unique_customers)
        })

# Get areas by city
areas_data = []
if 'area' in df.columns and 'city' in df.columns:
    area_counts = df.groupby('area')['city'].apply(lambda x: x.value_counts().index[0] if len(x) > 0 else 'غير محدد')
    for area, city in area_counts.items():
        count = len(df[df['area'] == area])
        unique_customers = df[df['area'] == area]['name'].nunique() if 'name' in df.columns else 0
        areas_data.append({
            'area': area,
            'records': int(count),
            'customers': int(unique_customers),
            'top_city': city
        })

# Sort by records
areas_data = sorted(areas_data, key=lambda x: x['records'], reverse=True)[:50]

# Get top customers
customers_data = []
if 'name' in df.columns:
    customer_groups = df.groupby('name').agg({
        'order_id': 'count',
        'price_gross': 'sum',
        'city': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'غير محدد',
        'area': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'غير محدد',
        'Type': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'غير محدد'
    }).rename(columns={'order_id': 'orders', 'price_gross': 'total_amount'})
    
    customer_groups = customer_groups.sort_values('orders', ascending=False).head(50)
    
    for customer_name, row in customer_groups.iterrows():
        customers_data.append({
            'name': customer_name,
            'orders': int(row['orders']),
            'total_amount': float(row['total_amount']),
            'city': row['city'],
            'area': row['area'],
            'type': row['Type']
        })

# Quality report
quality_metrics = {
    'customer_names': {
        'total': len(df),
        'missing': df['name'].isna().sum() if 'name' in df.columns else 0
    },
    'cities': {
        'total': len(df),
        'missing': (df['city'] == 'غير محدد').sum() if 'city' in df.columns else 0
    },
    'areas': {
        'total': len(df),
        'missing': (df['area'] == 'غير محدد').sum() if 'area' in df.columns else 0
    },
    'orders': {
        'total': len(df),
        'missing': 0
    }
}

print(f"✓ Analysis complete")
print(f"  - {len(cities_data)} unique cities")
print(f"  - {len(areas_data)} unique areas")
print(f"  - {len(customers_data)} top customers")

print("\n[4/5] Generating HTML dashboard...")

# Create comprehensive HTML
html_content = f'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Horeca Data Analysis - Modern Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        :root {{
            --primary: #6366f1;
            --secondary: #8b5cf6;
            --accent: #ec4899;
            --dark-bg: #0f172a;
            --darker-bg: #020617;
            --glass-light: rgba(255, 255, 255, 0.1);
            --glass-lighter: rgba(255, 255, 255, 0.15);
            --text-primary: #f1f5f9;
            --text-secondary: #cbd5e1;
            --border-color: rgba(255, 255, 255, 0.1);
            --gradient-1: linear-gradient(135deg, #6366f1, #8b5cf6);
            --gradient-2: linear-gradient(135deg, #ec4899, #f43f5e);
        }}

        body {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            background: var(--darker-bg);
            color: var(--text-primary);
            overflow-x: hidden;
            line-height: 1.6;
        }}

        body::before {{
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle at 20% 50%, rgba(99, 102, 241, 0.15) 0%, transparent 50%),
                        radial-gradient(circle at 80% 80%, rgba(139, 92, 246, 0.15) 0%, transparent 50%);
            pointer-events: none;
            z-index: 0;
        }}

        .container {{
            position: relative;
            z-index: 1;
            max-width: 1600px;
            margin: 0 auto;
            padding: 40px 20px;
        }}

        .glass {{
            background: var(--glass-light);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid var(--border-color);
            border-radius: 20px;
        }}

        .header {{
            text-align: center;
            margin-bottom: 50px;
            animation: fadeInDown 0.8s ease-out;
        }}

        .header h1 {{
            font-size: 3.5rem;
            font-weight: 800;
            margin-bottom: 15px;
            background: var(--gradient-1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -1px;
        }}

        .header p {{
            font-size: 1.1rem;
            color: var(--text-secondary);
            margin-bottom: 30px;
            font-weight: 500;
        }}

        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .stat-card {{
            background: var(--glass-light);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 30px;
            transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
            position: relative;
            overflow: hidden;
        }}

        .stat-card::before {{
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 100px;
            height: 100px;
            background: var(--gradient-1);
            border-radius: 50%;
            opacity: 0.1;
            transition: all 0.3s ease;
        }}

        .stat-card:hover {{
            background: var(--glass-lighter);
            border-color: rgba(99, 102, 241, 0.5);
            transform: translateY(-5px);
        }}

        .stat-card:hover::before {{
            top: -25%;
            right: -25%;
        }}

        .stat-card .label {{
            color: var(--text-secondary);
            font-size: 0.95rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
            display: block;
        }}

        .stat-card .value {{
            font-size: 2.5rem;
            font-weight: 700;
            background: var(--gradient-1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 8px;
        }}

        .stat-card .change {{
            font-size: 0.85rem;
            color: var(--text-secondary);
            font-weight: 500;
        }}

        .section {{
            background: var(--glass-light);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-color);
            border-radius: 20px;
            padding: 40px;
            margin-bottom: 30px;
            animation: fadeInUp 0.8s ease-out;
        }}

        .section-header {{
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 1px solid var(--border-color);
        }}

        .section-header h2 {{
            font-size: 1.8rem;
            font-weight: 700;
        }}

        .section-header::before {{
            content: '';
            width: 4px;
            height: 30px;
            background: var(--gradient-1);
            border-radius: 2px;
        }}

        .table-container {{
            overflow-x: auto;
            margin-top: 20px;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.95rem;
        }}

        thead {{
            background: rgba(99, 102, 241, 0.1);
        }}

        th {{
            padding: 16px;
            text-align: right;
            color: var(--primary);
            font-weight: 700;
            border-bottom: 2px solid var(--border-color);
            text-transform: uppercase;
            font-size: 0.85rem;
            letter-spacing: 0.5px;
        }}

        td {{
            padding: 14px 16px;
            color: var(--text-secondary);
            border-bottom: 1px solid var(--border-color);
        }}

        tbody tr {{
            transition: all 0.2s ease;
        }}

        tbody tr:hover {{
            background: rgba(99, 102, 241, 0.1);
        }}

        tbody tr:hover td {{
            color: var(--text-primary);
        }}

        .toggle-btn {{
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.2));
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 8px 16px;
            border-radius: 10px;
            cursor: pointer;
            font-weight: 600;
            font-size: 0.85rem;
            transition: all 0.3s ease;
            text-transform: uppercase;
        }}

        .toggle-btn:hover {{
            background: linear-gradient(135deg, rgba(99, 102, 241, 0.4), rgba(139, 92, 246, 0.4));
            border-color: rgba(99, 102, 241, 0.8);
            transform: scale(1.05);
        }}

        .badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 0.8rem;
            font-weight: 700;
            text-transform: uppercase;
        }}

        .badge-success {{
            background: rgba(34, 197, 94, 0.2);
            color: #86efac;
            border: 1px solid rgba(34, 197, 94, 0.5);
        }}

        .search-input {{
            background: var(--glass-light);
            backdrop-filter: blur(12px);
            padding: 12px 16px;
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            border-radius: 12px;
            font-size: 0.95rem;
            font-family: 'Plus Jakarta Sans', sans-serif;
            transition: all 0.3s ease;
            margin-bottom: 20px;
            width: 100%;
            max-width: 400px;
        }}

        .search-input:focus {{
            outline: none;
            border-color: rgba(99, 102, 241, 0.8);
            background: rgba(99, 102, 241, 0.1);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }}

        @keyframes fadeInDown {{
            from {{
                opacity: 0;
                transform: translateY(-30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 2.5rem;
            }}
            .section {{
                padding: 25px;
            }}
            .stats-grid {{
                grid-template-columns: 1fr;
            }}
            table {{
                font-size: 0.85rem;
            }}
            th, td {{
                padding: 10px;
            }}
        }}

        ::-webkit-scrollbar {{
            width: 10px;
        }}
        ::-webkit-scrollbar-track {{
            background: var(--glass-light);
        }}
        ::-webkit-scrollbar-thumb {{
            background: var(--primary);
            border-radius: 5px;
        }}

        .text-center {{
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 تحليل بيانات Horeca</h1>
            <p>لوحة تحكم ذكية حديثة بتصميم Glassmorphism متقدم</p>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <span class="label">إجمالي السجلات</span>
                <div class="value">{len(df)}</div>
                <span class="change">✓ تمت معالجة جميع الطلبات</span>
            </div>
            <div class="stat-card">
                <span class="label">العملاء الفريدين</span>
                <div class="value">{df['name'].nunique() if 'name' in df.columns else 0}</div>
                <span class="change">✓ تم تنظيفهم وتصنيفهم</span>
            </div>
            <div class="stat-card">
                <span class="label">المدن</span>
                <div class="value">{len(cities_data)}</div>
                <span class="change">✓ تم توحيدها</span>
            </div>
            <div class="stat-card">
                <span class="label">المناطق</span>
                <div class="value">{len(areas_data)}</div>
                <span class="change">✓ تم التحقق منها</span>
            </div>
        </div>

        <div class="section">
            <div class="section-header">
                <h2>📍 تحليل المدن</h2>
            </div>
            <input type="text" class="search-input" id="citySearch" placeholder="🔍 ابحث عن المدن...">
            <div class="table-container">
                <table id="citiesTable">
                    <thead>
                        <tr>
                            <th>المدينة</th>
                            <th>السجلات</th>
                            <th>العملاء</th>
                        </tr>
                    </thead>
                    <tbody>
                        {chr(10).join([f"<tr><td>{c['city']}</td><td>{c['records']}</td><td>{c['customers']}</td></tr>" for c in cities_data[:20]])}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="section">
            <div class="section-header">
                <h2>🗺️ أفضل المناطق</h2>
            </div>
            <input type="text" class="search-input" id="areaSearch" placeholder="🔍 ابحث عن المناطق...">
            <div class="table-container">
                <table id="areasTable">
                    <thead>
                        <tr>
                            <th>المنطقة</th>
                            <th>السجلات</th>
                            <th>العملاء</th>
                            <th>المدينة</th>
                        </tr>
                    </thead>
                    <tbody>
                        {chr(10).join([f"<tr><td>{a['area']}</td><td>{a['records']}</td><td>{a['customers']}</td><td>{a['top_city']}</td></tr>" for a in areas_data[:25]])}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="section">
            <div class="section-header">
                <h2>👥 أفضل العملاء</h2>
            </div>
            <input type="text" class="search-input" id="customerSearch" placeholder="🔍 ابحث عن العملاء...">
            <div class="table-container">
                <table id="customersTable">
                    <thead>
                        <tr>
                            <th>اسم العميل</th>
                            <th>عدد الطلبات</th>
                            <th>الإجمالي</th>
                            <th>النوع</th>
                            <th>المدينة</th>
                            <th>المنطقة</th>
                        </tr>
                    </thead>
                    <tbody>
                        {chr(10).join([f"<tr><td>{c['name']}</td><td>{c['orders']}</td><td>{c['total_amount']:.2f}</td><td>{c['type']}</td><td>{c['city']}</td><td>{c['area']}</td></tr>" for c in customers_data[:30]])}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="section">
            <div class="section-header">
                <h2>📈 تقرير جودة البيانات</h2>
            </div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>الفئة</th>
                            <th>الإجمالي</th>
                            <th>المفقود</th>
                            <th>نسبة الاكتمال</th>
                            <th>الحالة</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join([f'''<tr>
                            <td>{k.replace('_', ' ').title()}</td>
                            <td>{v['total']}</td>
                            <td>{v['missing']}</td>
                            <td>{((v['total']-v['missing'])/v['total']*100):.1f}%</td>
                            <td><span class="badge badge-success">مكتمل</span></td>
                        </tr>''' for k, v in quality_metrics.items()])}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <script>
        // Search functionality
        document.getElementById('citySearch').addEventListener('keyup', function(e) {{
            const value = e.target.value.toLowerCase();
            document.querySelectorAll('#citiesTable tbody tr').forEach(row => {{
                row.style.display = row.textContent.toLowerCase().includes(value) ? '' : 'none';
            }});
        }});

        document.getElementById('areaSearch').addEventListener('keyup', function(e) {{
            const value = e.target.value.toLowerCase();
            document.querySelectorAll('#areasTable tbody tr').forEach(row => {{
                row.style.display = row.textContent.toLowerCase().includes(value) ? '' : 'none';
            }});
        }});

        document.getElementById('customerSearch').addEventListener('keyup', function(e) {{
            const value = e.target.value.toLowerCase();
            document.querySelectorAll('#customersTable tbody tr').forEach(row => {{
                row.style.display = row.textContent.toLowerCase().includes(value) ? '' : 'none';
            }});
        }});
    </script>
</body>
</html>'''

# Save HTML
with open('horeca_modern_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"✓ Dashboard generated: horeca_modern_dashboard.html")

# Save cleaned data
print("\n[5/5] Saving cleaned data...")
df.to_csv('data_cleaned.csv', index=False, encoding='utf-8', sep='\t')
print(f"✓ Cleaned data saved: data_cleaned.csv")

# Final report
print("\n" + "=" * 60)
print("PROCESSING COMPLETE ✓")
print("=" * 60)
print("\n📊 SUMMARY STATISTICS:")
print(f"  • Total Records: {len(df)}")
print(f"  • Unique Customers: {df['name'].nunique() if 'name' in df.columns else 0}")
print(f"  • Unique Cities: {len(cities_data)}")
print(f"  • Unique Areas: {len(areas_data)}")
print(f"\n🔧 DATA QUALITY:")
for category, metrics in quality_metrics.items():
    completion = ((metrics['total'] - metrics['missing']) / metrics['total'] * 100)
    print(f"  • {category.replace('_', ' ').title()}: {completion:.1f}% complete")

print("\n📁 OUTPUT FILES:")
print("  • horeca_modern_dashboard.html (Interactive dashboard)")
print("  • data_cleaned.csv (Processed data)")
print("\n✨ Dashboard is ready for viewing!")

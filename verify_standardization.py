import pandas as pd

df = pd.read_csv('data_cleaned.csv', sep='\t')

print("=" * 70)
print("STANDARDIZATION VERIFICATION")
print("=" * 70)

print("\n📍 CITIES (محافظة):")
cities = sorted(df['city'].unique())
for city in cities:
    count = len(df[df['city'] == city])
    print(f"  • {city}: {count} سجل")

print("\n\n📝 TYPES (الأنواع):")
types_data = df['Type'].value_counts().to_dict()
for type_name, count in sorted(types_data.items(), key=lambda x: x[1], reverse=True)[:20]:
    print(f"  • {type_name}: {count} سجل")

print("\n\n👥 TOP CUSTOMERS:")
customers = df.groupby('name').size().nlargest(10)
for customer, count in customers.items():
    print(f"  • {customer}: {count} طلب")

print("\n" + "=" * 70)

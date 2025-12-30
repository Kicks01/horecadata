import json

try:
    with open('dashboard_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    customers = data.get('customers', [])
    print(f'✓ Customers in JSON: {len(customers)}')
    if customers:
        print(f'  First customer: {customers[0].get("name", "N/A")}')
        print(f'  Last customer: {customers[-1].get("name", "N/A")}')
except Exception as e:
    print(f'✗ Error: {e}')

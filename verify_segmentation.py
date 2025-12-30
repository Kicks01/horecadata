import json

with open('dashboard_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

customers = data.get('customers', [])
segments = data.get('segments', [])

print(f"Total customers: {len(customers)}")
print(f"Total segments: {len(segments)}\n")

# Check for missing segmentation
missing_segment = 0
missing_color = 0
missing_reason = 0

for customer in customers:
    if 'segment' not in customer or not customer['segment']:
        missing_segment += 1
    if 'segment_color' not in customer or not customer['segment_color']:
        missing_color += 1
    if 'segment_reason' not in customer or not customer['segment_reason']:
        missing_reason += 1

print("Segmentation Status:")
print(f"  Customers with segment: {len(customers) - missing_segment} / {len(customers)}")
print(f"  Customers with segment_color: {len(customers) - missing_color} / {len(customers)}")
print(f"  Customers with segment_reason: {len(customers) - missing_reason} / {len(customers)}")

if missing_segment == 0 and missing_color == 0 and missing_reason == 0:
    print("\n✓ All customers have complete segmentation data!")
else:
    print(f"\n✗ Missing data: {missing_segment} segments, {missing_color} colors, {missing_reason} reasons")

print("\nSegments Distribution:")
for seg in segments:
    print(f"  {seg['name']}: {seg['count']} customers, GMV: {seg['gmv']:,.2f}")

print("\nSample Customer:")
sample = customers[0]
print(f"  Name: {sample['name']}")
print(f"  Segment: {sample.get('segment', 'N/A')}")
print(f"  Color: {sample.get('segment_color', 'N/A')}")
print(f"  Reason: {sample.get('segment_reason', 'N/A')}")


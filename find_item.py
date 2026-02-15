import json

with open('prompt data/clothing/clothing_list.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total items: {len(data.get('items', []))}")

# Find upper_body items
upper_body_items = []
for item in data.get('items', []):
    if item.get('body_part') == 'upper_body':
        upper_body_items.append(item)

print(f"Upper body items: {len(upper_body_items)}")
if upper_body_items:
    print("\nFirst 5 upper_body items:")
    for i, item in enumerate(upper_body_items[:5]):
        print(f"  {i+1}. ID: {item.get('id')}, Name: {item.get('name')}")
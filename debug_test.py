import sys
import tempfile
import json
from pathlib import Path
from generator.prompt_generator import PromptGenerator

# Create test data directory
temp_dir = Path(tempfile.mkdtemp())

# Create clothing catalog
clothing_dir = temp_dir / "clothing"
clothing_dir.mkdir(parents=True, exist_ok=True)

clothing_catalog = {
    "category": "clothing",
    "items": [
        {"id": "shirt", "name": "shirt", "body_part": "upper_body"},
        {"id": "pants", "name": "pants", "body_part": "lower_body", "covers_legs": True},
        {"id": "hat", "name": "hat", "body_part": "head"}
    ],
    "index_by_body_part": {
        "upper_body": ["shirt"],
        "lower_body": ["pants"],
        "head": ["hat"]
    }
}

with open(clothing_dir / "clothing_list.json", "w", encoding="utf-8") as f:
    json.dump(clothing_catalog, f, indent=2)

# Create color catalog
colors_dir = temp_dir / "colors"
colors_dir.mkdir(parents=True, exist_ok=True)

color_catalog = {
    "palettes": [
        {
            "id": "test_palette",
            "name": "Test Palette",
            "colors": ["red", "blue", "green"]
        }
    ],
    "individual_colors": ["red", "blue", "green", "yellow"],
    "individual_colors_i18n": {
        "red": {"en": "red", "zh": "红色"},
        "blue": {"en": "blue", "zh": "蓝色"},
        "green": {"en": "green", "zh": "绿色"},
        "yellow": {"en": "yellow", "zh": "黄色"}
    }
}

with open(colors_dir / "color_palettes.json", "w", encoding="utf-8") as f:
    json.dump(color_catalog, f, indent=2)

# Create generator
gen = PromptGenerator(data_dir=temp_dir)

# Test getting slot options
print("Testing upper_body slot options:")
options = gen.get_slot_options("upper_body")
print(f"Options: {options}")

# Test resolving a value
print("\nTesting resolve_slot_value_name for upper_body with shirt:")
result = gen.resolve_slot_value_name("upper_body", "shirt", "shirt", "en")
print(f"Result: {result}")

# Test localizing color
print("\nTesting localize_color_token for blue:")
color_result = gen.localize_color_token("blue", "en")
print(f"Result: {color_result}")

# Cleanup
import shutil
shutil.rmtree(temp_dir)
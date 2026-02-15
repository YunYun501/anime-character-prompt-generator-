"""
Pytest configuration and fixtures for Random Character Prompt Generator tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import json
from generator.prompt_generator import PromptGenerator


@pytest.fixture
def temp_data_dir():
    """Create a temporary directory with minimal test catalogs."""
    temp_dir = tempfile.mkdtemp()
    
    # Create directory structure
    for subdir in ["hair", "eyes", "body", "clothing", "colors", "expressions", "poses", "view_angles", "backgrounds"]:
        (Path(temp_dir) / subdir).mkdir(parents=True, exist_ok=True)
    
    # Create minimal hair catalog
    hair_catalog = {
        "category": "hair",
        "items": [
            {"id": "ponytail", "name": "ponytail", "category": "style"},
            {"id": "long_hair", "name": "long hair", "category": "length"},
            {"id": "black_hair", "name": "black hair", "category": "color"},
            {"id": "straight_hair", "name": "straight hair", "category": "texture"}
        ],
        "index_by_category": {
            "style": ["ponytail"],
            "length": ["long_hair"],
            "color": ["black_hair"],
            "texture": ["straight_hair"]
        }
    }
    
    with open(Path(temp_dir) / "hair" / "hair_catalog.json", "w", encoding="utf-8") as f:
        json.dump(hair_catalog, f, indent=2)
    
    # Create minimal clothing catalog
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
    
    with open(Path(temp_dir) / "clothing" / "clothing_list.json", "w", encoding="utf-8") as f:
        json.dump(clothing_catalog, f, indent=2)
    
    # Create minimal color catalog
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
    
    with open(Path(temp_dir) / "colors" / "color_palettes.json", "w", encoding="utf-8") as f:
        json.dump(color_catalog, f, indent=2)
    
    # Create minimal body features catalog
    body_catalog = {
        "category": "body",
        "items": [
            {"id": "slim", "name": "slim", "category": "body_type"},
            {"id": "tall", "name": "tall", "category": "height"}
        ],
        "index_by_category": {
            "body_type": ["slim"],
            "height": ["tall"]
        }
    }
    
    with open(Path(temp_dir) / "body" / "body_features.json", "w", encoding="utf-8") as f:
        json.dump(body_catalog, f, indent=2)
    
    # Create minimal expressions catalog
    expressions_catalog = {
        "category": "expressions",
        "items": [
            {"id": "smile", "name": "smile"},
            {"id": "neutral", "name": "neutral"}
        ]
    }
    
    with open(Path(temp_dir) / "expressions" / "female_expressions.json", "w", encoding="utf-8") as f:
        json.dump(expressions_catalog, f, indent=2)
    
    # Create minimal poses catalog
    poses_catalog = {
        "category": "poses",
        "items": [
            {"id": "standing", "name": "standing"},
            {"id": "sitting", "name": "sitting", "uses_hands": True}
        ],
        "index_by_category": {
            "gesture": []
        }
    }
    
    with open(Path(temp_dir) / "poses" / "poses.json", "w", encoding="utf-8") as f:
        json.dump(poses_catalog, f, indent=2)
    
    # Create minimal backgrounds catalog
    backgrounds_catalog = {
        "category": "backgrounds",
        "items": [
            {"id": "indoor", "name": "indoor"},
            {"id": "outdoor", "name": "outdoor"}
        ]
    }
    
    with open(Path(temp_dir) / "backgrounds" / "backgrounds.json", "w", encoding="utf-8") as f:
        json.dump(backgrounds_catalog, f, indent=2)
    
    # Create minimal view angles catalog
    view_angles_catalog = {
        "category": "view_angles",
        "items": [
            {"id": "front_view", "name": "front view"},
            {"id": "side_view", "name": "side view"}
        ]
    }
    
    with open(Path(temp_dir) / "view_angles" / "view_angles.json", "w", encoding="utf-8") as f:
        json.dump(view_angles_catalog, f, indent=2)
    
    # Create minimal eyes catalog
    eyes_catalog = {
        "category": "eyes",
        "items": [
            {"id": "blue_eyes", "name": "blue eyes", "category": "color"},
            {"id": "sparkling_eyes", "name": "sparkling eyes", "category": "expression_quality"}
        ],
        "index_by_category": {
            "color": ["blue_eyes"],
            "expression_quality": ["sparkling_eyes"],
            "eye_shape": [],
            "pupil_state": [],
            "eye_state": [],
            "eye_accessories": []
        }
    }
    
    with open(Path(temp_dir) / "eyes" / "eye_catalog.json", "w", encoding="utf-8") as f:
        json.dump(eyes_catalog, f, indent=2)
    
    yield Path(temp_dir)
    
    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def test_generator(temp_data_dir):
    """Create a PromptGenerator instance with test data."""
    return PromptGenerator(data_dir=temp_data_dir)


@pytest.fixture
def sample_slot_state():
    """Return sample slot state for testing."""
    return {
        "hair_style": {
            "enabled": True,
            "value_id": "ponytail",
            "value": "ponytail",
            "color": None,
            "weight": 1.0
        },
        "upper_body": {
            "enabled": True,
            "value_id": "shirt",
            "value": "shirt",
            "color": "blue",
            "weight": 1.5
        },
        "background": {
            "enabled": True,
            "value_id": "indoor",
            "value": "indoor",
            "color": None,
            "weight": 1.0
        }
    }
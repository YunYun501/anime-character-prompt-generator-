"""
Tests for the prompt generator core functionality.
"""

import pytest
from pathlib import Path
from generator.prompt_generator import PromptGenerator, SlotConfig, GeneratorConfig


class TestPromptGenerator:
    """Test the PromptGenerator class."""
    
    def test_init(self, test_generator):
        """Test generator initialization."""
        gen = test_generator
        assert gen.data_dir.exists()
        assert "clothing" in gen.catalogs
        assert "hair" in gen.catalogs
        assert "colors" in gen.catalogs
        
    def test_slot_definitions(self):
        """Test slot definitions are loaded correctly."""
        # This tests the class-level definitions, not instance
        assert "hair_style" in PromptGenerator.SLOT_DEFINITIONS
        assert "upper_body" in PromptGenerator.SLOT_DEFINITIONS
        assert "background" in PromptGenerator.SLOT_DEFINITIONS
        
        # Check slot properties
        hair_slot = PromptGenerator.SLOT_DEFINITIONS["hair_style"]
        assert hair_slot["category"] == "appearance"
        assert hair_slot["catalog"] == "hair"
        
    def test_get_slot_options(self, test_generator):
        """Test getting slot options."""
        gen = test_generator
        options = gen.get_slot_options("hair_style")
        assert isinstance(options, list)
        assert len(options) > 0
        
        # Check option structure
        option = options[0]
        assert "id" in option
        assert "name" in option
        
    def test_sample_slot(self, test_generator):
        """Test sampling a random slot value."""
        gen = test_generator
        item = gen.sample_slot("hair_style")
        assert item is not None
        assert "id" in item
        assert "name" in item
        
    def test_get_palette_list(self, test_generator):
        """Test getting color palettes."""
        gen = test_generator
        palettes = gen.get_palette_list()
        assert isinstance(palettes, list)
        if palettes:  # If there are palettes defined
            palette = palettes[0]
            assert "id" in palette
            assert "name" in palette
            
    def test_sample_color_from_palette(self, test_generator):
        """Test sampling colors from palette."""
        gen = test_generator
        palettes = gen.get_palette_list()
        if palettes:
            color = gen.sample_color_from_palette(palettes[0]["id"])
            assert color is not None
            assert isinstance(color, str)


class TestSlotConfig:
    """Test the SlotConfig dataclass."""
    
    def test_defaults(self):
        """Test default values."""
        slot = SlotConfig()
        assert slot.enabled is True
        assert slot.locked is False
        assert slot.value is None
        assert slot.value_id is None
        assert slot.color is None
        assert slot.color_enabled is False
        assert slot.weight == 1.0
        
    def test_to_dict(self):
        """Test serialization to dict."""
        slot = SlotConfig(
            enabled=False,
            locked=True,
            value_id="test_id",
            color="blue",
            weight=1.5
        )
        data = slot.to_dict()
        assert data["enabled"] is False
        assert data["locked"] is True
        assert data["value_id"] == "test_id"
        assert data["color"] == "blue"
        assert data["weight"] == 1.5
        
    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "enabled": False,
            "locked": True,
            "value": "test_value",
            "value_id": "test_id",
            "color": "red",
            "color_enabled": True,
            "weight": 2.0
        }
        slot = SlotConfig.from_dict(data)
        assert slot.enabled is False
        assert slot.locked is True
        assert slot.value == "test_value"
        assert slot.value_id == "test_id"
        assert slot.color == "red"
        assert slot.color_enabled is True
        assert slot.weight == 2.0


class TestGeneratorConfig:
    """Test the GeneratorConfig dataclass."""
    
    def test_defaults(self):
        """Test default values."""
        config = GeneratorConfig()
        assert config.name == "Untitled"
        assert config.color_mode == "none"
        assert config.active_palette_id is None
        assert config.full_body_mode is True
        assert config.slots == {}
        
    def test_with_slots(self):
        """Test config with slots."""
        config = GeneratorConfig()
        config.slots["hair_style"] = SlotConfig(value_id="ponytail")
        config.slots["upper_body"] = SlotConfig(value_id="shirt", color="blue")
        
        assert len(config.slots) == 2
        assert config.slots["hair_style"].value_id == "ponytail"
        assert config.slots["upper_body"].color == "blue"
        
    def test_to_dict(self):
        """Test serialization to dict."""
        config = GeneratorConfig()
        config.slots["test_slot"] = SlotConfig(value_id="test_id")
        data = config.to_dict()
        
        assert "name" in data
        assert "created_at" in data
        assert "color_mode" in data
        assert "slots" in data
        assert "test_slot" in data["slots"]
        
    def test_from_dict(self):
        """Test deserialization from dict."""
        data = {
            "name": "Test Config",
            "color_mode": "palette",
            "active_palette_id": "pastel",
            "full_body_mode": False,
            "slots": {
                "hair_style": {
                    "enabled": True,
                    "value_id": "ponytail"
                }
            }
        }
        config = GeneratorConfig.from_dict(data)
        assert config.name == "Test Config"
        assert config.color_mode == "palette"
        assert config.active_palette_id == "pastel"
        assert config.full_body_mode is False
        assert "hair_style" in config.slots
        assert config.slots["hair_style"].value_id == "ponytail"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
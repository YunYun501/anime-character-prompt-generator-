"""State management for the Reflex prompt generator."""

import reflex as rx
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import sys

# Add project root to path for importing generator
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from generator.prompt_generator import PromptGenerator, SlotConfig, GeneratorConfig


# Slot definitions - mirrors the Gradio version
APPEARANCE_SLOTS = ["hair_style", "hair_length", "hair_color", "hair_texture", "eye_color", "eye_style"]
BODY_SLOTS = ["body_type", "height", "skin", "age_appearance", "special_features", "expression", "pose", "gesture"]
CLOTHING_LEFT = ["head", "neck", "upper_body", "waist", "lower_body", "full_body"]
CLOTHING_RIGHT = ["outerwear", "hands", "legs", "feet", "accessory", "background"]
CLOTHING_SLOTS = CLOTHING_LEFT + CLOTHING_RIGHT
ALL_SLOTS = APPEARANCE_SLOTS + BODY_SLOTS + CLOTHING_SLOTS

# Global generator instance (shared across state)
_global_generator: Optional[PromptGenerator] = None

def get_generator() -> PromptGenerator:
    """Get or create the global generator instance."""
    global _global_generator
    if _global_generator is None:
        _global_generator = PromptGenerator()
    return _global_generator


class AppState(rx.State):
    """Main application state."""
    
    # Slot states - stored as dict for each slot
    slots: Dict[str, Dict[str, Any]] = {}
    
    # Precomputed slot options for each slot (loaded at init)
    slot_options: Dict[str, List[str]] = {}
    
    # Color options list
    color_options: List[str] = []
    
    # Palette options list
    palette_options: List[str] = []
    
    # Settings
    full_body_mode: bool = True
    color_mode: str = "None"  # "None", "Palette", "Random"
    selected_palette: str = "(None)"
    
    # Output
    generated_prompt: str = ""
    
    # Save/Load
    config_name: str = ""
    saved_configs: List[str] = []
    save_status: str = ""
    
    # UI state
    save_load_open: bool = False
    
    def initialize(self):
        """Initialize the app state with default values."""
        generator = get_generator()
        
        # Initialize all slots
        for slot_name in ALL_SLOTS:
            self.slots[slot_name] = {
                "enabled": True,
                "constant": False,
                "value": "(None)",
                "color": "(No Color)",
                "weight": 1.0,
            }
        
        # Precompute slot options
        for slot_name in ALL_SLOTS:
            options = generator.get_slot_option_names(slot_name)
            self.slot_options[slot_name] = ["(None)"] + options
        
        # Compute color options
        colors = generator.individual_colors.copy()
        if not colors:
            colors = ["white", "black", "red", "blue", "pink", "purple",
                     "green", "yellow", "orange", "brown", "grey", "silver", "gold"]
        self.color_options = ["(No Color)"] + colors
        
        # Compute palette options
        palette_names = generator.get_palette_names()
        self.palette_options = ["(None)"] + palette_names
        
        # Load saved configs list
        self.refresh_configs()
    
    # ===== SLOT EVENT HANDLERS =====
    
    def toggle_slot_enabled(self, slot_name: str):
        """Toggle enabled state for a slot."""
        if slot_name in self.slots:
            current = self.slots[slot_name]["enabled"]
            self.slots[slot_name] = {**self.slots[slot_name], "enabled": not current}
    
    def toggle_slot_constant(self, slot_name: str):
        """Toggle constant (locked) state for a slot."""
        if slot_name in self.slots:
            current = self.slots[slot_name]["constant"]
            self.slots[slot_name] = {**self.slots[slot_name], "constant": not current}
    
    def set_slot_value(self, slot_name: str, value: str):
        """Set the value for a slot."""
        if slot_name in self.slots:
            self.slots[slot_name] = {**self.slots[slot_name], "value": value}
    
    def set_slot_color(self, slot_name: str, color: str):
        """Set the color for a slot."""
        if slot_name in self.slots:
            self.slots[slot_name] = {**self.slots[slot_name], "color": color}
    
    def set_slot_weight(self, slot_name: str, weight: str):
        """Set the weight for a slot."""
        if slot_name in self.slots:
            try:
                w = float(weight) if weight else 1.0
            except ValueError:
                w = 1.0
            self.slots[slot_name] = {**self.slots[slot_name], "weight": w}
    
    def randomize_slot(self, slot_name: str):
        """Randomize a single slot's value and color."""
        generator = get_generator()
        
        if slot_name not in self.slots:
            return
        
        slot_data = self.slots[slot_name]
        if slot_data["constant"]:
            return
        
        # Randomize value
        item = generator.sample_slot(slot_name)
        new_value = item.get("name", "(None)") if item else "(None)"
        
        # Randomize color if applicable
        new_color = "(No Color)"
        has_color = generator.SLOT_DEFINITIONS.get(slot_name, {}).get("has_color", False)
        if has_color:
            new_color = self._get_random_color()
        
        self.slots[slot_name] = {
            **slot_data,
            "value": new_value,
            "color": new_color,
        }
    
    def randomize_slot_color(self, slot_name: str):
        """Randomize just the color for a slot."""
        if slot_name not in self.slots:
            return
        
        new_color = self._get_random_color()
        self.slots[slot_name] = {**self.slots[slot_name], "color": new_color}
    
    def _get_random_color(self) -> str:
        """Get a random color based on current color mode."""
        generator = get_generator()
        
        if self.color_mode == "Palette" and self.selected_palette != "(None)":
            # Find palette ID
            for p in generator.palettes.values():
                if p.get("name") == self.selected_palette:
                    color = generator.sample_color_from_palette(p["id"])
                    return color if color else "(No Color)"
            return "(No Color)"
        elif self.color_mode == "Random":
            color = generator.sample_random_color()
            return color if color else "(No Color)"
        else:
            return "(No Color)"
    
    # ===== SECTION HANDLERS =====
    
    def randomize_section(self, section: str):
        """Randomize all slots in a section."""
        slots = []
        if section == "appearance":
            slots = APPEARANCE_SLOTS
        elif section == "body":
            slots = BODY_SLOTS
        elif section == "clothing":
            slots = CLOTHING_SLOTS
        
        for slot_name in slots:
            self.randomize_slot(slot_name)
    
    def disable_section(self, section: str):
        """Disable all slots in a section."""
        slots = []
        if section == "appearance":
            slots = APPEARANCE_SLOTS
        elif section == "body":
            slots = BODY_SLOTS
        elif section == "clothing":
            slots = CLOTHING_SLOTS
        
        for slot_name in slots:
            if slot_name in self.slots:
                self.slots[slot_name] = {**self.slots[slot_name], "enabled": False}
    
    def enable_section(self, section: str):
        """Enable all slots in a section."""
        slots = []
        if section == "appearance":
            slots = APPEARANCE_SLOTS
        elif section == "body":
            slots = BODY_SLOTS
        elif section == "clothing":
            slots = CLOTHING_SLOTS
        
        for slot_name in slots:
            if slot_name in self.slots:
                self.slots[slot_name] = {**self.slots[slot_name], "enabled": True}
    
    # ===== GLOBAL HANDLERS =====
    
    def randomize_all(self):
        """Randomize all non-constant slots and generate prompt."""
        generator = get_generator()
        
        full_body_value = None
        
        for slot_name in ALL_SLOTS:
            if slot_name not in self.slots:
                continue
            
            slot_data = self.slots[slot_name]
            if slot_data["constant"]:
                continue
            
            # Randomize value
            item = generator.sample_slot(slot_name)
            new_value = item.get("name", "(None)") if item else "(None)"
            
            # Track full_body for logic
            if slot_name == "full_body":
                full_body_value = new_value
            
            # Apply full-body logic
            if self.full_body_mode and slot_name in ["upper_body", "lower_body"]:
                if full_body_value and full_body_value != "(None)":
                    new_value = "(None)"
            
            # Randomize color if applicable
            new_color = "(No Color)"
            has_color = generator.SLOT_DEFINITIONS.get(slot_name, {}).get("has_color", False)
            if has_color:
                new_color = self._get_random_color()
            
            self.slots[slot_name] = {
                **slot_data,
                "value": new_value,
                "color": new_color,
            }
        
        # Auto-generate prompt
        self.generate_prompt()
    
    def reset_all(self):
        """Reset all slots to default values (not enabled/constant state)."""
        for slot_name in ALL_SLOTS:
            if slot_name in self.slots:
                self.slots[slot_name] = {
                    **self.slots[slot_name],
                    "value": "(None)",
                    "color": "(No Color)",
                    "weight": 1.0,
                }
        self.generated_prompt = ""
    
    def generate_prompt(self):
        """Generate the prompt from current slot values."""
        parts = ["1girl"]
        
        # Define slot order for prompt building
        slot_order = [
            "hair_color", "hair_length", "hair_style", "hair_texture",
            "eye_color", "eye_style",
            "body_type", "height", "skin", "age_appearance", "special_features",
            "expression",
            "full_body", "head", "neck", "upper_body", "waist", "lower_body",
            "outerwear", "hands", "legs", "feet", "accessory",
            "pose", "gesture",
            "background"
        ]
        
        for slot_name in slot_order:
            if slot_name not in self.slots:
                continue
            
            slot_data = self.slots[slot_name]
            if not slot_data["enabled"]:
                continue
            
            value = slot_data["value"]
            if not value or value == "(None)":
                continue
            
            # Skip upper/lower body if full_body is active
            if self.full_body_mode and slot_name in ["upper_body", "lower_body"]:
                full_body_data = self.slots.get("full_body", {})
                if full_body_data.get("enabled") and full_body_data.get("value") not in [None, "(None)"]:
                    continue
            
            # Build prompt part
            color = slot_data["color"]
            if color and color != "(No Color)":
                prompt_part = f"{color} {value}"
            else:
                prompt_part = value
            
            # Add weight if not default
            weight = slot_data["weight"]
            if weight != 1.0:
                prompt_part = f"({prompt_part}:{weight:.1f})"
            
            parts.append(prompt_part)
        
        self.generated_prompt = ", ".join(parts)
    
    def set_generated_prompt(self, value: str):
        """Set the generated prompt (for manual editing)."""
        self.generated_prompt = value
    
    # ===== SETTINGS HANDLERS =====
    
    def set_full_body_mode(self, value: bool):
        """Set full-body mode."""
        self.full_body_mode = value
    
    def set_color_mode(self, mode: str):
        """Set color mode."""
        self.color_mode = mode
    
    def set_palette(self, palette: str):
        """Set selected palette and auto-enable palette mode."""
        self.selected_palette = palette
        if palette and palette != "(None)":
            self.color_mode = "Palette"
    
    # ===== SAVE/LOAD HANDLERS =====
    
    def set_config_name(self, name: str):
        """Set the config name for saving."""
        self.config_name = name
    
    def toggle_save_load(self):
        """Toggle the save/load section visibility."""
        self.save_load_open = not self.save_load_open
    
    def refresh_configs(self):
        """Refresh the list of saved configurations."""
        generator = get_generator()
        configs_dir = generator.data_dir / "configs"
        if configs_dir.exists():
            self.saved_configs = [f.stem for f in configs_dir.glob("*.json")]
        else:
            self.saved_configs = []
    
    def save_config(self):
        """Save current configuration to file."""
        generator = get_generator()
        
        if not self.config_name or self.config_name.strip() == "":
            self.save_status = "Please enter a configuration name"
            return
        
        config = GeneratorConfig(name=self.config_name.strip())
        config.created_at = datetime.now().isoformat()
        config.color_mode = self.color_mode.lower() if self.color_mode != "None" else "none"
        config.full_body_mode = self.full_body_mode
        
        for slot_name in ALL_SLOTS:
            if slot_name in self.slots:
                slot_data = self.slots[slot_name]
                slot_config = SlotConfig(
                    enabled=slot_data["enabled"],
                    locked=slot_data["constant"],
                    value=slot_data["value"] if slot_data["value"] != "(None)" else None,
                    color=slot_data["color"] if slot_data["color"] != "(No Color)" else None,
                    color_enabled=slot_data["color"] not in [None, "(No Color)"],
                    weight=slot_data["weight"],
                )
                config.slots[slot_name] = slot_config
        
        configs_dir = generator.data_dir / "configs"
        configs_dir.mkdir(exist_ok=True)
        filepath = configs_dir / f"{self.config_name.strip()}.json"
        generator.save_config(config, filepath)
        
        self.save_status = f"Saved: {self.config_name}"
        self.refresh_configs()
    
    def load_config(self, config_name: str):
        """Load a configuration from file."""
        generator = get_generator()
        
        if not config_name:
            self.save_status = "Please select a config"
            return
        
        configs_dir = generator.data_dir / "configs"
        filepath = configs_dir / f"{config_name}.json"
        
        if not filepath.exists():
            self.save_status = f"Config not found: {config_name}"
            return
        
        try:
            config = generator.load_config(filepath)
            
            # Apply to state
            for slot_name in ALL_SLOTS:
                slot_config = config.slots.get(slot_name, SlotConfig())
                self.slots[slot_name] = {
                    "enabled": slot_config.enabled,
                    "constant": slot_config.locked,
                    "value": slot_config.value or "(None)",
                    "color": slot_config.color or "(No Color)",
                    "weight": slot_config.weight if slot_config.weight else 1.0,
                }
            
            self.full_body_mode = config.full_body_mode
            self.color_mode = config.color_mode.title() if config.color_mode != "none" else "None"
            
            self.save_status = f"Loaded: {config_name}"
        except Exception as e:
            self.save_status = f"Error: {str(e)}"

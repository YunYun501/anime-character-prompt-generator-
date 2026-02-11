"""Main Reflex application for Random Character Prompt Generator."""

import reflex as rx
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from generator.prompt_generator import PromptGenerator


# Slot definitions
APPEARANCE_SLOTS = ["hair_style", "hair_length", "hair_color", "hair_texture", "eye_color", "eye_style"]
BODY_SLOTS = ["body_type", "height", "skin", "age_appearance", "special_features", "expression", "pose", "gesture"]
CLOTHING_LEFT = ["head", "neck", "upper_body", "waist", "lower_body", "full_body"]
CLOTHING_RIGHT = ["outerwear", "hands", "legs", "feet", "accessory", "background"]
CLOTHING_SLOTS = CLOTHING_LEFT + CLOTHING_RIGHT
ALL_SLOTS = APPEARANCE_SLOTS + BODY_SLOTS + CLOTHING_SLOTS

# Global generator
_generator = None

def get_generator():
    global _generator
    if _generator is None:
        _generator = PromptGenerator()
    return _generator


class AppState(rx.State):
    """Application state."""
    
    # Generated prompt
    generated_prompt: str = ""
    
    # Settings
    full_body_mode: bool = True
    color_mode: str = "None"
    
    # Simple slot storage - just values
    slot_values: dict[str, str] = {}
    slot_colors: dict[str, str] = {}
    slot_enabled: dict[str, bool] = {}
    
    def initialize(self):
        """Initialize slots."""
        for slot_name in ALL_SLOTS:
            self.slot_values[slot_name] = "(None)"
            self.slot_colors[slot_name] = "(No Color)"
            self.slot_enabled[slot_name] = True
    
    def randomize_all(self):
        """Randomize all slots."""
        gen = get_generator()
        for slot_name in ALL_SLOTS:
            item = gen.sample_slot(slot_name)
            if item:
                self.slot_values[slot_name] = item.get("name", "(None)")
            else:
                self.slot_values[slot_name] = "(None)"
        self.generate_prompt()
    
    def generate_prompt(self):
        """Generate the prompt."""
        parts = ["1girl"]
        for slot_name in ALL_SLOTS:
            value = self.slot_values.get(slot_name, "(None)")
            enabled = self.slot_enabled.get(slot_name, True)
            if enabled and value and value != "(None)":
                color = self.slot_colors.get(slot_name, "(No Color)")
                if color and color != "(No Color)":
                    parts.append(f"{color} {value}")
                else:
                    parts.append(value)
        self.generated_prompt = ", ".join(parts)
    
    def reset_all(self):
        """Reset all slots."""
        for slot_name in ALL_SLOTS:
            self.slot_values[slot_name] = "(None)"
            self.slot_colors[slot_name] = "(No Color)"
        self.generated_prompt = ""
    
    def set_prompt(self, value: str):
        """Set prompt text."""
        self.generated_prompt = value


def index() -> rx.Component:
    """Main page."""
    return rx.box(
        rx.heading("🎨 Random Anime Character Prompt Generator", size="7"),
        
        # Prompt output
        rx.box(
            rx.heading("Generated Prompt", size="5"),
            rx.text_area(
                value=AppState.generated_prompt,
                on_change=AppState.set_prompt,
                rows="4",
                width="100%",
            ),
            rx.hstack(
                rx.button("✨ Generate", on_click=AppState.generate_prompt, color_scheme="blue"),
                rx.button("🎲 Randomize All", on_click=AppState.randomize_all, color_scheme="green"),
                rx.button("🔄 Reset", on_click=AppState.reset_all),
                rx.button("📋 Copy", on_click=rx.set_clipboard(AppState.generated_prompt)),
                spacing="3",
            ),
            padding="15px",
            border="1px solid #e5e7eb",
            border_radius="8px",
            margin_bottom="15px",
        ),
        
        # Simple slot display (just show what slots exist)
        rx.box(
            rx.text("Slots: " + ", ".join(ALL_SLOTS[:6]) + "... (total: " + str(len(ALL_SLOTS)) + ")"),
            padding="10px",
            background="#f5f5f5",
            border_radius="4px",
        ),
        
        on_mount=AppState.initialize,
        padding="20px",
        max_width="1200px",
        margin="0 auto",
    )


app = rx.App()
app.add_page(index, title="Character Prompt Generator")

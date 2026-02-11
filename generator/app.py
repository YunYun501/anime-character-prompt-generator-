"""
Gradio Web UI for Random Character Prompt Generator.

Features:
- Per-slot: Randomize button, Dropdown, Color button, Disable toggle, Weight input
- Section randomize buttons
- Full-body toggle logic
- Color palette system
- Save/Load configurations
"""

import gradio as gr
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json
from datetime import datetime

from .prompt_generator import PromptGenerator, SlotConfig, GeneratorConfig


class PromptGeneratorUI:
    """Gradio-based UI for the prompt generator."""
    
    def __init__(self, generator: Optional[PromptGenerator] = None):
        """Initialize the UI."""
        if generator is None:
            generator = PromptGenerator()
        self.generator = generator
        self.config = generator.create_default_config()
        self.configs_dir = generator.data_dir / "configs"
        self.configs_dir.mkdir(exist_ok=True)
        
        # Track UI component references
        self.slot_components: Dict[str, Dict[str, Any]] = {}
    
    def get_slot_choices(self, slot_name: str) -> List[str]:
        """Get choices for a slot dropdown, including 'None' option."""
        options = self.generator.get_slot_option_names(slot_name)
        return ["(None)"] + options
    
    def get_color_choices(self) -> List[str]:
        """Get color choices from palettes or individual colors."""
        colors = self.generator.individual_colors.copy()
        if not colors:
            colors = ["white", "black", "red", "blue", "pink", "purple", 
                     "green", "yellow", "orange", "brown", "grey", "silver", "gold"]
        return ["(No Color)"] + colors
    
    def get_palette_choices(self) -> List[str]:
        """Get palette choices for dropdown."""
        names = self.generator.get_palette_names()
        return ["(None)"] + names
    
    def get_saved_configs(self) -> List[str]:
        """Get list of saved configuration names."""
        configs = self.generator.list_saved_configs(self.configs_dir)
        return ["(Select Config)"] + configs
    
    def randomize_single_slot(self, slot_name: str, current_value: str, 
                              color_enabled: bool, palette_name: str) -> Tuple[str, str]:
        """Randomize a single slot and return new value and color."""
        # Find palette ID from name
        palette_id = None
        if palette_name != "(None)":
            for p in self.generator.palettes.values():
                if p.get("name") == palette_name:
                    palette_id = p["id"]
                    break
        
        item = self.generator.sample_slot(slot_name)
        new_value = item.get("name", "(None)") if item else "(None)"
        
        # Sample color if enabled
        new_color = "(No Color)"
        if color_enabled and self.generator.SLOT_DEFINITIONS.get(slot_name, {}).get("has_color", False):
            if palette_id:
                new_color = self.generator.sample_color_from_palette(palette_id) or "(No Color)"
            else:
                new_color = self.generator.sample_random_color() or "(No Color)"
        
        return new_value, new_color
    
    def build_prompt_from_ui(self, *args) -> str:
        """Build prompt from all UI component values."""
        # This will be connected to all slot components
        # args come in order based on how we connect them
        parts = ["1girl"]
        
        # Parse args based on slot order
        slot_names = list(self.generator.SLOT_DEFINITIONS.keys())
        idx = 0
        
        for slot_name in slot_names:
            if idx + 4 > len(args):
                break
            
            enabled = args[idx]
            value = args[idx + 1]
            color = args[idx + 2]
            weight = args[idx + 3]
            
            idx += 4
            
            if not enabled or value == "(None)" or not value:
                continue
            
            # Build part
            part = ""
            if color and color != "(No Color)":
                part = f"{color} {value}"
            else:
                part = value
            
            # Add weight if not 1.0
            try:
                w = float(weight)
                if w != 1.0:
                    part = f"({part}:{w:.1f})"
            except:
                pass
            
            parts.append(part)
        
        return ", ".join(parts)
    
    def save_config_handler(self, config_name: str, *slot_values) -> str:
        """Save current configuration to file."""
        if not config_name or config_name.strip() == "":
            return "Please enter a configuration name"
        
        # Build config from UI values
        config = GeneratorConfig(name=config_name.strip())
        config.created_at = datetime.now().isoformat()
        
        slot_names = list(self.generator.SLOT_DEFINITIONS.keys())
        idx = 0
        
        for slot_name in slot_names:
            if idx + 4 > len(slot_values):
                break
            
            enabled = slot_values[idx]
            value = slot_values[idx + 1]
            color = slot_values[idx + 2]
            weight = slot_values[idx + 3]
            
            idx += 4
            
            slot_config = SlotConfig(
                enabled=bool(enabled),
                value=value if value != "(None)" else None,
                color=color if color != "(No Color)" else None,
                color_enabled=bool(color and color != "(No Color)"),
                weight=float(weight) if weight else 1.0
            )
            config.slots[slot_name] = slot_config
        
        # Save to file
        filepath = self.configs_dir / f"{config_name.strip()}.json"
        self.generator.save_config(config, filepath)
        
        return f"Saved configuration: {config_name}"
    
    def load_config_handler(self, config_name: str) -> List:
        """Load configuration and return values for all UI components."""
        if config_name == "(Select Config)" or not config_name:
            # Return current defaults
            return self._get_default_ui_values()
        
        filepath = self.configs_dir / f"{config_name}.json"
        if not filepath.exists():
            return self._get_default_ui_values()
        
        config = self.generator.load_config(filepath)
        
        # Build output values in slot order
        values = []
        slot_names = list(self.generator.SLOT_DEFINITIONS.keys())
        
        for slot_name in slot_names:
            slot = config.slots.get(slot_name, SlotConfig())
            values.extend([
                slot.enabled,  # checkbox
                slot.value or "(None)",  # dropdown
                slot.color or "(No Color)",  # color dropdown
                slot.weight or 1.0  # weight number
            ])
        
        return values
    
    def _get_default_ui_values(self) -> List:
        """Get default values for all UI components."""
        values = []
        for slot_name in self.generator.SLOT_DEFINITIONS.keys():
            values.extend([
                True,  # enabled
                "(None)",  # value
                "(No Color)",  # color
                1.0  # weight
            ])
        return values
    
    def create_slot_row(self, slot_name: str, slot_def: dict) -> Tuple:
        """Create a row of components for a single slot."""
        display_name = slot_name.replace("_", " ").title()
        has_color = slot_def.get("has_color", False)
        
        with gr.Row():
            enabled = gr.Checkbox(value=True, label="", scale=1, min_width=30)
            dropdown = gr.Dropdown(
                choices=self.get_slot_choices(slot_name),
                value="(None)",
                label=display_name,
                scale=4
            )
            random_btn = gr.Button("🎲", scale=1, min_width=40)
            
            if has_color:
                color_dropdown = gr.Dropdown(
                    choices=self.get_color_choices(),
                    value="(No Color)",
                    label="Color",
                    scale=2
                )
                color_random_btn = gr.Button("🎨", scale=1, min_width=40)
            else:
                color_dropdown = gr.Dropdown(
                    choices=["(No Color)"],
                    value="(No Color)",
                    label="Color",
                    scale=2,
                    visible=False
                )
                color_random_btn = gr.Button("🎨", scale=1, min_width=40, visible=False)
            
            weight = gr.Number(value=1.0, label="Weight", scale=1, minimum=0.1, maximum=2.0, step=0.1)
        
        return enabled, dropdown, color_dropdown, weight, random_btn, color_random_btn
    
    def build_ui(self) -> gr.Blocks:
        """Build the complete Gradio UI."""
        
        with gr.Blocks(title="Random Character Prompt Generator", theme=gr.themes.Soft()) as app:
            gr.Markdown("# Random Character Prompt Generator for Stable Diffusion")
            gr.Markdown("Generate diverse anime female character prompts with randomization and fine control.")
            
            # Store all slot components for event handling
            all_enabled = []
            all_dropdowns = []
            all_colors = []
            all_weights = []
            all_random_btns = []
            all_color_btns = []
            slot_names_list = list(self.generator.SLOT_DEFINITIONS.keys())
            
            # Global Controls
            with gr.Row():
                with gr.Column(scale=2):
                    randomize_all_btn = gr.Button("🎲 Randomize All", variant="primary", size="lg")
                with gr.Column(scale=2):
                    reset_btn = gr.Button("🔄 Reset All", size="lg")
                with gr.Column(scale=1):
                    full_body_mode = gr.Checkbox(value=True, label="Full-body mode (auto-disable upper/lower)")
            
            # Color Palette Section
            with gr.Row():
                color_mode = gr.Radio(
                    choices=["None", "Palette", "Random"],
                    value="None",
                    label="Color Mode"
                )
                palette_dropdown = gr.Dropdown(
                    choices=self.get_palette_choices(),
                    value="(None)",
                    label="Color Palette",
                    visible=False
                )
                random_palette_btn = gr.Button("🎲 Random Palette", visible=False)
            
            # Show/hide palette controls based on color mode
            def update_palette_visibility(mode):
                return gr.update(visible=(mode == "Palette")), gr.update(visible=(mode == "Palette"))
            
            color_mode.change(
                fn=update_palette_visibility,
                inputs=[color_mode],
                outputs=[palette_dropdown, random_palette_btn]
            )
            
            # Sections with their slots
            sections = {
                "appearance": ("👤 Appearance", ["hair_style", "hair_length", "hair_color", "hair_texture", "eye_color", "eye_style"]),
                "body": ("🧍 Body", ["body_type", "height", "skin", "age_appearance", "special_features"]),
                "expression": ("😊 Expression", ["expression"]),
                "clothing": ("👗 Clothing", ["head", "neck", "upper_body", "waist", "lower_body", "full_body", "outerwear", "hands", "legs", "feet", "accessory"]),
                "pose": ("🎭 Pose", ["pose", "gesture"]),
                "background": ("🖼️ Background", ["background"]),
            }
            
            section_components = {}
            
            for section_id, (section_title, section_slots) in sections.items():
                with gr.Accordion(section_title, open=True):
                    with gr.Row():
                        section_random_btn = gr.Button(f"🎲 Randomize {section_title.split(' ')[1]}", size="sm")
                        section_disable_btn = gr.Button(f"❌ Disable All", size="sm")
                        section_enable_btn = gr.Button(f"✅ Enable All", size="sm")
                    
                    section_enabled_list = []
                    section_dropdown_list = []
                    section_color_list = []
                    section_weight_list = []
                    section_random_list = []
                    section_color_btn_list = []
                    
                    for slot_name in section_slots:
                        if slot_name not in self.generator.SLOT_DEFINITIONS:
                            continue
                        
                        slot_def = self.generator.SLOT_DEFINITIONS[slot_name]
                        enabled, dropdown, color_dd, weight, rand_btn, color_btn = self.create_slot_row(slot_name, slot_def)
                        
                        all_enabled.append(enabled)
                        all_dropdowns.append(dropdown)
                        all_colors.append(color_dd)
                        all_weights.append(weight)
                        all_random_btns.append(rand_btn)
                        all_color_btns.append(color_btn)
                        
                        section_enabled_list.append(enabled)
                        section_dropdown_list.append(dropdown)
                        section_color_list.append(color_dd)
                        section_weight_list.append(weight)
                        section_random_list.append((rand_btn, slot_name))
                        section_color_btn_list.append((color_btn, slot_name))
                    
                    section_components[section_id] = {
                        "enabled": section_enabled_list,
                        "dropdowns": section_dropdown_list,
                        "colors": section_color_list,
                        "weights": section_weight_list,
                        "random_btn": section_random_btn,
                        "disable_btn": section_disable_btn,
                        "enable_btn": section_enable_btn,
                        "slots": section_slots
                    }
            
            # Output Section
            gr.Markdown("---")
            gr.Markdown("## Generated Prompt")
            
            with gr.Row():
                output_prompt = gr.Textbox(
                    label="Prompt",
                    lines=3,
                    max_lines=5,
                    interactive=True
                )
            
            with gr.Row():
                copy_btn = gr.Button("📋 Copy to Clipboard", size="lg")
                generate_btn = gr.Button("✨ Generate Prompt", variant="primary", size="lg")
            
            # Save/Load Section
            gr.Markdown("---")
            gr.Markdown("## Save / Load Configuration")
            
            with gr.Row():
                config_name_input = gr.Textbox(label="Configuration Name", placeholder="Enter name to save...")
                save_btn = gr.Button("💾 Save Config", size="lg")
            
            with gr.Row():
                load_dropdown = gr.Dropdown(
                    choices=self.get_saved_configs(),
                    value="(Select Config)",
                    label="Load Configuration"
                )
                load_btn = gr.Button("📂 Load Config", size="lg")
                refresh_configs_btn = gr.Button("🔄", size="lg", min_width=50)
            
            save_status = gr.Textbox(label="Status", interactive=False)
            
            # ===== EVENT HANDLERS =====
            
            # All components for prompt building
            all_components = []
            for i in range(len(all_enabled)):
                all_components.extend([all_enabled[i], all_dropdowns[i], all_colors[i], all_weights[i]])
            
            # Generate prompt button
            def generate_prompt(*args):
                parts = ["1girl"]
                idx = 0
                for slot_name in slot_names_list:
                    if idx + 4 > len(args):
                        break
                    enabled, value, color, weight = args[idx:idx+4]
                    idx += 4
                    
                    if not enabled or value == "(None)" or not value:
                        continue
                    
                    part = f"{color} {value}" if color and color != "(No Color)" else value
                    
                    try:
                        w = float(weight)
                        if w != 1.0:
                            part = f"({part}:{w:.1f})"
                    except:
                        pass
                    
                    parts.append(part)
                
                return ", ".join(parts)
            
            generate_btn.click(
                fn=generate_prompt,
                inputs=all_components,
                outputs=[output_prompt]
            )
            
            # Randomize All
            def randomize_all_handler(palette_name, color_mode_val, full_body_on, *current_values):
                outputs = []
                palette_id = None
                
                if color_mode_val == "Palette" and palette_name != "(None)":
                    for p in self.generator.palettes.values():
                        if p.get("name") == palette_name:
                            palette_id = p["id"]
                            break
                
                # Process each slot
                full_body_value = None
                
                for i, slot_name in enumerate(slot_names_list):
                    item = self.generator.sample_slot(slot_name)
                    new_val = item.get("name", "(None)") if item else "(None)"
                    
                    # Track full_body value
                    if slot_name == "full_body":
                        full_body_value = new_val
                    
                    # Handle full body mode
                    if full_body_on and slot_name in ["upper_body", "lower_body"]:
                        if full_body_value and full_body_value != "(None)":
                            new_val = "(None)"
                    
                    # Color
                    new_color = "(No Color)"
                    has_color = self.generator.SLOT_DEFINITIONS[slot_name].get("has_color", False)
                    if has_color:
                        if color_mode_val == "Palette" and palette_id:
                            new_color = self.generator.sample_color_from_palette(palette_id) or "(No Color)"
                        elif color_mode_val == "Random":
                            new_color = self.generator.sample_random_color() or "(No Color)"
                    
                    outputs.extend([new_val, new_color])
                
                return outputs
            
            # Build outputs list for randomize all
            randomize_all_outputs = []
            for i in range(len(all_dropdowns)):
                randomize_all_outputs.extend([all_dropdowns[i], all_colors[i]])
            
            randomize_all_btn.click(
                fn=randomize_all_handler,
                inputs=[palette_dropdown, color_mode, full_body_mode],
                outputs=randomize_all_outputs
            )
            
            # Reset All
            def reset_all_handler():
                outputs = []
                for _ in slot_names_list:
                    outputs.extend([True, "(None)", "(No Color)", 1.0])
                return outputs
            
            reset_btn.click(
                fn=reset_all_handler,
                inputs=[],
                outputs=all_components
            )
            
            # Section buttons
            for section_id, section_data in section_components.items():
                slots = section_data["slots"]
                enabled_list = section_data["enabled"]
                dropdown_list = section_data["dropdowns"]
                color_list = section_data["colors"]
                
                # Section randomize
                def make_section_randomize(slots_list, dd_list, clr_list):
                    def handler(palette_name, color_mode_val):
                        outputs = []
                        palette_id = None
                        
                        if color_mode_val == "Palette" and palette_name != "(None)":
                            for p in self.generator.palettes.values():
                                if p.get("name") == palette_name:
                                    palette_id = p["id"]
                                    break
                        
                        for slot_name in slots_list:
                            if slot_name not in self.generator.SLOT_DEFINITIONS:
                                continue
                            
                            item = self.generator.sample_slot(slot_name)
                            new_val = item.get("name", "(None)") if item else "(None)"
                            
                            new_color = "(No Color)"
                            has_color = self.generator.SLOT_DEFINITIONS[slot_name].get("has_color", False)
                            if has_color:
                                if color_mode_val == "Palette" and palette_id:
                                    new_color = self.generator.sample_color_from_palette(palette_id) or "(No Color)"
                                elif color_mode_val == "Random":
                                    new_color = self.generator.sample_random_color() or "(No Color)"
                            
                            outputs.extend([new_val, new_color])
                        
                        return outputs
                    return handler
                
                section_outputs = []
                for i in range(len(dropdown_list)):
                    section_outputs.extend([dropdown_list[i], color_list[i]])
                
                section_data["random_btn"].click(
                    fn=make_section_randomize(slots, dropdown_list, color_list),
                    inputs=[palette_dropdown, color_mode],
                    outputs=section_outputs
                )
                
                # Section disable all
                def make_disable_handler(enabled_comps):
                    def handler():
                        return [False] * len(enabled_comps)
                    return handler
                
                section_data["disable_btn"].click(
                    fn=make_disable_handler(enabled_list),
                    inputs=[],
                    outputs=enabled_list
                )
                
                # Section enable all
                def make_enable_handler(enabled_comps):
                    def handler():
                        return [True] * len(enabled_comps)
                    return handler
                
                section_data["enable_btn"].click(
                    fn=make_enable_handler(enabled_list),
                    inputs=[],
                    outputs=enabled_list
                )
            
            # Per-slot random buttons
            for i, (btn, slot_name) in enumerate(zip(all_random_btns, slot_names_list)):
                def make_slot_random(sn, idx):
                    def handler(palette_name, color_mode_val):
                        item = self.generator.sample_slot(sn)
                        new_val = item.get("name", "(None)") if item else "(None)"
                        
                        new_color = "(No Color)"
                        has_color = self.generator.SLOT_DEFINITIONS[sn].get("has_color", False)
                        if has_color:
                            palette_id = None
                            if color_mode_val == "Palette" and palette_name != "(None)":
                                for p in self.generator.palettes.values():
                                    if p.get("name") == palette_name:
                                        palette_id = p["id"]
                                        break
                            
                            if palette_id:
                                new_color = self.generator.sample_color_from_palette(palette_id) or "(No Color)"
                            elif color_mode_val == "Random":
                                new_color = self.generator.sample_random_color() or "(No Color)"
                        
                        return new_val, new_color
                    return handler
                
                btn.click(
                    fn=make_slot_random(slot_name, i),
                    inputs=[palette_dropdown, color_mode],
                    outputs=[all_dropdowns[i], all_colors[i]]
                )
            
            # Per-slot color random buttons
            for i, (btn, slot_name) in enumerate(zip(all_color_btns, slot_names_list)):
                def make_color_random(sn, idx):
                    def handler(palette_name, color_mode_val):
                        has_color = self.generator.SLOT_DEFINITIONS[sn].get("has_color", False)
                        if not has_color:
                            return "(No Color)"
                        
                        palette_id = None
                        if color_mode_val == "Palette" and palette_name != "(None)":
                            for p in self.generator.palettes.values():
                                if p.get("name") == palette_name:
                                    palette_id = p["id"]
                                    break
                        
                        if palette_id:
                            return self.generator.sample_color_from_palette(palette_id) or "(No Color)"
                        else:
                            return self.generator.sample_random_color() or "(No Color)"
                    return handler
                
                btn.click(
                    fn=make_color_random(slot_name, i),
                    inputs=[palette_dropdown, color_mode],
                    outputs=[all_colors[i]]
                )
            
            # Save config
            save_btn.click(
                fn=self.save_config_handler,
                inputs=[config_name_input] + all_components,
                outputs=[save_status]
            )
            
            # Load config
            def load_config_ui(config_name):
                if config_name == "(Select Config)" or not config_name:
                    return self._get_default_ui_values()
                
                filepath = self.configs_dir / f"{config_name}.json"
                if not filepath.exists():
                    return self._get_default_ui_values()
                
                try:
                    config = self.generator.load_config(filepath)
                    values = []
                    
                    for slot_name in slot_names_list:
                        slot = config.slots.get(slot_name, SlotConfig())
                        values.extend([
                            slot.enabled,
                            slot.value or "(None)",
                            slot.color or "(No Color)",
                            slot.weight if slot.weight else 1.0
                        ])
                    
                    return values
                except Exception as e:
                    print(f"Error loading config: {e}")
                    return self._get_default_ui_values()
            
            load_btn.click(
                fn=load_config_ui,
                inputs=[load_dropdown],
                outputs=all_components
            )
            
            # Refresh configs list
            def refresh_configs():
                return gr.update(choices=self.get_saved_configs())
            
            refresh_configs_btn.click(
                fn=refresh_configs,
                inputs=[],
                outputs=[load_dropdown]
            )
            
            # Copy button - just shows instruction (Gradio handles clipboard differently)
            def copy_instruction(prompt):
                return prompt  # Gradio textbox is already copyable
            
            copy_btn.click(
                fn=copy_instruction,
                inputs=[output_prompt],
                outputs=[output_prompt]
            )
            
            # Random palette button
            def random_palette():
                palettes = self.generator.get_palette_names()
                if not palettes:
                    return "(None)"
                import random
                return random.choice(palettes)
            
            random_palette_btn.click(
                fn=random_palette,
                inputs=[],
                outputs=[palette_dropdown]
            )
        
        return app


def create_app() -> gr.Blocks:
    """Create and return the Gradio app."""
    ui = PromptGeneratorUI()
    return ui.build_ui()


if __name__ == "__main__":
    app = create_app()
    app.launch()

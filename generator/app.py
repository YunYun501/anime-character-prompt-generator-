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
import random as rand_module
from datetime import datetime
import os
import signal

from .prompt_generator import PromptGenerator, SlotConfig, GeneratorConfig


def shutdown_server():
    """Shutdown the Gradio server."""
    print("\nShutting down server...")
    os.kill(os.getpid(), signal.SIGTERM)


# Custom CSS for compact, centered layout
CUSTOM_CSS = """
/* Use full width */
.gradio-container {
    max-width: 100% !important;
    padding: 10px 20px !important;
}

/* Slot row - horizontal layout */
.slot-row {
    display: flex !important;
    align-items: center !important;
    gap: 10px !important;
    padding: 6px 10px !important;
    margin: 2px 0 !important;
    border-radius: 6px !important;
}

/* Enabled state - green */
.slot-enabled {
    border: 2px solid #22c55e !important;
    background-color: rgba(34, 197, 94, 0.08) !important;
}
.slot-enabled label {
    color: #16a34a !important;
    font-weight: 600 !important;
}

/* Disabled state - red/grey */
.slot-disabled {
    border: 2px solid #ef4444 !important;
    background-color: rgba(239, 68, 68, 0.08) !important;
    opacity: 0.5 !important;
}
.slot-disabled label {
    color: #9ca3af !important;
}

/* Output box */
#prompt-output textarea {
    font-size: 14px !important;
    font-family: monospace !important;
}

/* Column headers */
.column-header {
    font-weight: bold !important;
    font-size: 1.1em !important;
    padding: 8px !important;
    border-bottom: 2px solid #ddd !important;
    margin-bottom: 8px !important;
}
"""


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
        return configs if configs else []
    
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

    def build_ui(self) -> gr.Blocks:
        """Build the complete Gradio UI."""
        
        with gr.Blocks(css=CUSTOM_CSS, title="Character Prompt Generator") as app:
            gr.Markdown("# 🎨 Random Anime Character Prompt Generator")
            
            # Store all slot components for event handling
            all_enabled = []      # On/Off state (True/False)
            all_constant = []     # Constant state (True/False) - if True, skip during randomization
            all_dropdowns = []
            all_colors = []
            all_weights = []
            all_random_btns = []
            all_color_btns = []
            all_onoff_btns = []   # On/Off toggle buttons
            all_const_btns = []   # Constant toggle buttons
            
            # Define slot order matching our column layout
            appearance_slots = ["hair_style", "hair_length", "hair_color", "hair_texture", "eye_color", "eye_style"]
            body_slots = ["body_type", "height", "skin", "age_appearance", "special_features", "expression", "pose", "gesture"]
            clothing_slots = ["head", "neck", "upper_body", "waist", "lower_body", "full_body", "outerwear", "hands", "legs", "feet", "accessory", "background"]
            slot_names_list = appearance_slots + body_slots + clothing_slots
            
            # ===== GENERATE PROMPT SECTION (full row at top) =====
            gr.Markdown("## 📝 Generated Prompt")
            output_prompt = gr.Textbox(
                label="",
                lines=3,
                max_lines=5,
                interactive=True,
                elem_id="prompt-output",
                show_label=False
            )
            with gr.Row():
                generate_btn = gr.Button("✨ Generate Prompt", variant="primary", scale=2)
                randomize_all_btn = gr.Button("🎲 Randomize All", variant="secondary", scale=2)
                copy_btn = gr.Button("📋 Copy", scale=1)
                reset_btn = gr.Button("🔄 Reset", scale=1)
                shutdown_btn = gr.Button("⏹ Stop Server", variant="stop", scale=1)
            
            # ===== SETTINGS ROW =====
            with gr.Row():
                full_body_mode = gr.Checkbox(value=True, label="Full-body mode")
                color_mode = gr.Radio(
                    choices=["None", "Palette", "Random"],
                    value="None",
                    label="Color Mode"
                )
                palette_dropdown = gr.Dropdown(
                    choices=self.get_palette_choices(),
                    value="(None)",
                    label="Color Palette"
                )
            
            gr.Markdown("---")
            
            section_components = {}
            
            # Helper to create a slot row with On/Off and Constant buttons
            def create_slot_row(slot_name, has_color, display_name):
                row_id = f"slot-row-{slot_name}"
                
                # Hidden states
                enabled_state = gr.State(value=True)
                constant_state = gr.State(value=False)
                
                with gr.Group(elem_id=row_id, elem_classes=["slot-row", "slot-enabled"]):
                    with gr.Row():
                        onoff_btn = gr.Button("On", variant="primary", min_width=45, elem_classes="onoff-btn")
                        const_btn = gr.Button("🔓", min_width=35, elem_classes="const-btn")
                        dropdown = gr.Dropdown(
                            choices=self.get_slot_choices(slot_name),
                            value="(None)",
                            label=display_name,
                            scale=2
                        )
                        random_btn = gr.Button("🎲", min_width=35)
                        if has_color:
                            color_dropdown = gr.Dropdown(
                                choices=self.get_color_choices(),
                                value="(No Color)",
                                label="Color",
                                scale=1
                            )
                            color_random_btn = gr.Button("🎨", min_width=35)
                        else:
                            color_dropdown = gr.Dropdown(choices=["(No Color)"], value="(No Color)", visible=False)
                            color_random_btn = gr.Button("🎨", visible=False)
                        weight = gr.Number(value=1.0, label="Wt", minimum=0.1, maximum=2.0, step=0.1, min_width=50)
                
                return enabled_state, constant_state, onoff_btn, const_btn, dropdown, color_dropdown, color_random_btn, random_btn, weight
            
            # ===== ROW 1: Appearance (left) + Body (right) =====
            with gr.Row():
                # === COLUMN 1: Appearance ===
                with gr.Column(scale=1):
                    gr.Markdown("### 👤 Appearance")
                    with gr.Row():
                        section_random_btn_1 = gr.Button("🎲 Random", size="sm")
                        section_disable_btn_1 = gr.Button("❌ All Off", size="sm")
                        section_enable_btn_1 = gr.Button("✅ All On", size="sm")
                    section_enabled_1 = []
                    section_constant_1 = []
                    section_dropdown_1 = []
                    section_color_1 = []
                    section_weight_1 = []
                    
                    for slot_name in appearance_slots:
                        if slot_name not in self.generator.SLOT_DEFINITIONS:
                            continue
                        slot_def = self.generator.SLOT_DEFINITIONS[slot_name]
                        display_name = slot_name.replace("_", " ").title()
                        has_color = slot_def.get("has_color", False)
                        
                        enabled_state, constant_state, onoff_btn, const_btn, dropdown, color_dropdown, color_random_btn, random_btn, weight = create_slot_row(slot_name, has_color, display_name)
                        
                        all_enabled.append(enabled_state)
                        all_constant.append(constant_state)
                        all_onoff_btns.append((onoff_btn, slot_name))
                        all_const_btns.append((const_btn, slot_name))
                        all_dropdowns.append(dropdown)
                        all_colors.append(color_dropdown)
                        all_weights.append(weight)
                        all_random_btns.append((random_btn, slot_name))
                        all_color_btns.append((color_random_btn, slot_name))
                        section_enabled_1.append(enabled_state)
                        section_constant_1.append(constant_state)
                        section_dropdown_1.append(dropdown)
                        section_color_1.append(color_dropdown)
                        section_weight_1.append(weight)
                    
                    section_components["appearance"] = {
                        "enabled": section_enabled_1, "constant": section_constant_1,
                        "dropdowns": section_dropdown_1, "colors": section_color_1, "weights": section_weight_1,
                        "random_btn": section_random_btn_1, "disable_btn": section_disable_btn_1,
                        "enable_btn": section_enable_btn_1, "slots": appearance_slots
                    }
                
                # === COLUMN 2: Body & Expression & Pose ===
                with gr.Column(scale=1):
                    gr.Markdown("### 🧍 Body / Expression / Pose")
                    with gr.Row():
                        section_random_btn_2 = gr.Button("🎲 Random", size="sm")
                        section_disable_btn_2 = gr.Button("❌ All Off", size="sm")
                        section_enable_btn_2 = gr.Button("✅ All On", size="sm")
                    section_enabled_2 = []
                    section_constant_2 = []
                    section_dropdown_2 = []
                    section_color_2 = []
                    section_weight_2 = []
                    
                    for slot_name in body_slots:
                        if slot_name not in self.generator.SLOT_DEFINITIONS:
                            continue
                        slot_def = self.generator.SLOT_DEFINITIONS[slot_name]
                        display_name = slot_name.replace("_", " ").title()
                        has_color = slot_def.get("has_color", False)
                        
                        enabled_state, constant_state, onoff_btn, const_btn, dropdown, color_dropdown, color_random_btn, random_btn, weight = create_slot_row(slot_name, has_color, display_name)
                        
                        all_enabled.append(enabled_state)
                        all_constant.append(constant_state)
                        all_onoff_btns.append((onoff_btn, slot_name))
                        all_const_btns.append((const_btn, slot_name))
                        all_dropdowns.append(dropdown)
                        all_colors.append(color_dropdown)
                        all_weights.append(weight)
                        all_random_btns.append((random_btn, slot_name))
                        all_color_btns.append((color_random_btn, slot_name))
                        section_enabled_2.append(enabled_state)
                        section_constant_2.append(constant_state)
                        section_dropdown_2.append(dropdown)
                        section_color_2.append(color_dropdown)
                        section_weight_2.append(weight)
                    
                    section_components["body"] = {
                        "enabled": section_enabled_2, "constant": section_constant_2,
                        "dropdowns": section_dropdown_2, "colors": section_color_2, "weights": section_weight_2,
                        "random_btn": section_random_btn_2, "disable_btn": section_disable_btn_2,
                        "enable_btn": section_enable_btn_2, "slots": body_slots
                    }
            
            # ===== ROW 2: Clothing & Background =====
            gr.Markdown("### 👗 Clothing & Background")
            with gr.Row():
                section_random_btn_3 = gr.Button("🎲 Random Section", size="sm")
                section_disable_btn_3 = gr.Button("❌ All Off", size="sm")
                section_enable_btn_3 = gr.Button("✅ All On", size="sm")
            section_enabled_3 = []
            section_constant_3 = []
            section_dropdown_3 = []
            section_color_3 = []
            section_weight_3 = []
            
            # Split clothing into 2 columns for better layout
            with gr.Row():
                with gr.Column(scale=1):
                    clothing_left = ["head", "neck", "upper_body", "waist", "lower_body", "full_body"]
                    for slot_name in clothing_left:
                        if slot_name not in self.generator.SLOT_DEFINITIONS:
                            continue
                        slot_def = self.generator.SLOT_DEFINITIONS[slot_name]
                        display_name = slot_name.replace("_", " ").title()
                        has_color = slot_def.get("has_color", False)
                        
                        enabled_state, constant_state, onoff_btn, const_btn, dropdown, color_dropdown, color_random_btn, random_btn, weight = create_slot_row(slot_name, has_color, display_name)
                        
                        all_enabled.append(enabled_state)
                        all_constant.append(constant_state)
                        all_onoff_btns.append((onoff_btn, slot_name))
                        all_const_btns.append((const_btn, slot_name))
                        all_dropdowns.append(dropdown)
                        all_colors.append(color_dropdown)
                        all_weights.append(weight)
                        all_random_btns.append((random_btn, slot_name))
                        all_color_btns.append((color_random_btn, slot_name))
                        section_enabled_3.append(enabled_state)
                        section_constant_3.append(constant_state)
                        section_dropdown_3.append(dropdown)
                        section_color_3.append(color_dropdown)
                        section_weight_3.append(weight)
                
                with gr.Column(scale=1):
                    clothing_right = ["outerwear", "hands", "legs", "feet", "accessory", "background"]
                    for slot_name in clothing_right:
                        if slot_name not in self.generator.SLOT_DEFINITIONS:
                            continue
                        slot_def = self.generator.SLOT_DEFINITIONS[slot_name]
                        display_name = slot_name.replace("_", " ").title()
                        has_color = slot_def.get("has_color", False)
                        
                        enabled_state, constant_state, onoff_btn, const_btn, dropdown, color_dropdown, color_random_btn, random_btn, weight = create_slot_row(slot_name, has_color, display_name)
                        
                        all_enabled.append(enabled_state)
                        all_constant.append(constant_state)
                        all_onoff_btns.append((onoff_btn, slot_name))
                        all_const_btns.append((const_btn, slot_name))
                        all_dropdowns.append(dropdown)
                        all_colors.append(color_dropdown)
                        all_weights.append(weight)
                        all_random_btns.append((random_btn, slot_name))
                        all_color_btns.append((color_random_btn, slot_name))
                        section_enabled_3.append(enabled_state)
                        section_constant_3.append(constant_state)
                        section_dropdown_3.append(dropdown)
                        section_color_3.append(color_dropdown)
                        section_weight_3.append(weight)
            
            section_components["clothing"] = {
                "enabled": section_enabled_3, "constant": section_constant_3,
                "dropdowns": section_dropdown_3, "colors": section_color_3, "weights": section_weight_3,
                "random_btn": section_random_btn_3, "disable_btn": section_disable_btn_3,
                "enable_btn": section_enable_btn_3, "slots": clothing_slots
            }
            
            # ===== SAVE/LOAD SECTION =====
            with gr.Accordion("💾 Save / Load Configuration", open=False):
                with gr.Row():
                    config_name_input = gr.Textbox(label="Config Name", placeholder="my_character", scale=2)
                    save_btn = gr.Button("💾 Save", scale=1)
                with gr.Row():
                    load_dropdown = gr.Dropdown(
                        choices=self.get_saved_configs(),
                        value=None,
                        label="Load Config",
                        scale=2,
                        allow_custom_value=False
                    )
                    load_btn = gr.Button("📂 Load", scale=1)
                    refresh_configs_btn = gr.Button("🔄", scale=0, min_width=40)
                save_status = gr.Textbox(label="Status", interactive=False, max_lines=1)
            
            # ===== EVENT HANDLERS =====
            
            # On/Off button toggle handlers
            for i, (btn, slot_name) in enumerate(all_onoff_btns):
                row_id = f"slot-row-{slot_name}"
                
                def make_onoff_toggle(idx, rid):
                    def handler(current_state):
                        new_state = not current_state
                        btn_text = "On" if new_state else "Off"
                        btn_variant = "primary" if new_state else "secondary"
                        return new_state, gr.update(value=btn_text, variant=btn_variant)
                    return handler
                
                btn.click(
                    fn=make_onoff_toggle(i, row_id),
                    inputs=[all_enabled[i]],
                    outputs=[all_enabled[i], btn]
                )
            
            # Constant button toggle handlers  
            for i, (btn, slot_name) in enumerate(all_const_btns):
                def make_const_toggle(idx):
                    def handler(current_state):
                        new_state = not current_state
                        btn_text = "🔒" if new_state else "🔓"
                        return new_state, gr.update(value=btn_text)
                    return handler
                
                btn.click(
                    fn=make_const_toggle(i),
                    inputs=[all_constant[i]],
                    outputs=[all_constant[i], btn]
                )
            
            # Generate prompt function
            def generate_prompt(*args):
                # args = enabled states + dropdowns + colors + weights (interleaved)
                num_slots = len(slot_names_list)
                parts = ["1girl"]
                
                for i, slot_name in enumerate(slot_names_list):
                    enabled = args[i]  # First num_slots args are enabled states
                    value = args[num_slots + i]  # Next are dropdowns
                    color = args[num_slots * 2 + i]  # Next are colors
                    weight = args[num_slots * 3 + i]  # Last are weights
                    
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
                inputs=all_enabled + all_dropdowns + all_colors + all_weights, 
                outputs=[output_prompt]
            )
            
            # Randomize All - respects Constant flags, generates prompt immediately
            def randomize_all_handler(palette_name, color_mode_val, full_body_on, *args):
                # args = constant states + enabled states + current dropdowns + current colors + current weights
                num_slots = len(slot_names_list)
                constant_states = args[:num_slots]
                enabled_states = args[num_slots:num_slots*2]
                current_dropdowns = args[num_slots*2:num_slots*3]
                current_colors = args[num_slots*3:num_slots*4]
                
                outputs_dropdowns = []
                outputs_colors = []
                prompt_parts = ["1girl"]
                palette_id = None
                
                if color_mode_val == "Palette" and palette_name and palette_name != "(None)":
                    for p in self.generator.palettes.values():
                        if p.get("name") == palette_name:
                            palette_id = p["id"]
                            break
                
                full_body_value = None
                
                for i, slot_name in enumerate(slot_names_list):
                    is_constant = constant_states[i] if i < len(constant_states) else False
                    is_enabled = enabled_states[i] if i < len(enabled_states) else True
                    
                    # If constant, keep current value
                    if is_constant:
                        new_val = current_dropdowns[i] if i < len(current_dropdowns) else "(None)"
                        new_color = current_colors[i] if i < len(current_colors) else "(No Color)"
                    else:
                        # Randomize
                        item = self.generator.sample_slot(slot_name)
                        new_val = item.get("name", "(None)") if item else "(None)"
                        
                        if slot_name == "full_body":
                            full_body_value = new_val
                        
                        if full_body_on and slot_name in ["upper_body", "lower_body"]:
                            if full_body_value and full_body_value != "(None)":
                                new_val = "(None)"
                        
                        new_color = "(No Color)"
                        has_color = self.generator.SLOT_DEFINITIONS[slot_name].get("has_color", False)
                        if has_color:
                            if color_mode_val == "Palette" and palette_id:
                                new_color = self.generator.sample_color_from_palette(palette_id) or "(No Color)"
                            elif color_mode_val == "Random":
                                new_color = self.generator.sample_random_color() or "(No Color)"
                    
                    outputs_dropdowns.append(new_val)
                    outputs_colors.append(new_color)
                    
                    # Build prompt part if enabled
                    if is_enabled and new_val and new_val != "(None)":
                        part = f"{new_color} {new_val}" if new_color and new_color != "(No Color)" else new_val
                        prompt_parts.append(part)
                
                generated_prompt = ", ".join(prompt_parts)
                
                return outputs_dropdowns + outputs_colors + [generated_prompt]
            
            randomize_all_btn.click(
                fn=randomize_all_handler,
                inputs=[palette_dropdown, color_mode, full_body_mode] + all_constant + all_enabled + all_dropdowns + all_colors,
                outputs=all_dropdowns + all_colors + [output_prompt]
            )
            
            # Auto-enable Palette mode when selecting a palette
            def on_palette_select(palette_name):
                if palette_name and palette_name != "(None)":
                    return "Palette"
                return gr.update()
            
            palette_dropdown.change(
                fn=on_palette_select,
                inputs=[palette_dropdown],
                outputs=[color_mode]
            )
            
            # Reset All - resets dropdowns, colors, weights (not On/Off or Constant)
            def reset_all_handler():
                dropdowns = ["(None)"] * len(slot_names_list)
                colors = ["(No Color)"] * len(slot_names_list)
                weights = [1.0] * len(slot_names_list)
                return dropdowns + colors + weights
            
            reset_btn.click(
                fn=reset_all_handler, 
                inputs=[], 
                outputs=all_dropdowns + all_colors + all_weights
            )
            
            # Section buttons - randomize respects constant flags
            for section_id, section_data in section_components.items():
                slots = section_data["slots"]
                constant_list = section_data["constant"]
                dropdown_list = section_data["dropdowns"]
                color_list = section_data["colors"]
                
                # Section randomize
                def make_section_randomize(slots_list, const_list, dd_list, col_list):
                    def handler(palette_name, color_mode_val, *current_and_const):
                        # First half are constant states, second half are current dropdowns
                        n = len(slots_list)
                        const_states = current_and_const[:n]
                        current_dds = current_and_const[n:n*2]
                        current_cols = current_and_const[n*2:]
                        
                        outputs = []
                        palette_id = None
                        
                        if color_mode_val == "Palette" and palette_name and palette_name != "(None)":
                            for p in self.generator.palettes.values():
                                if p.get("name") == palette_name:
                                    palette_id = p["id"]
                                    break
                        
                        for i, slot_name in enumerate(slots_list):
                            if slot_name not in self.generator.SLOT_DEFINITIONS:
                                outputs.extend(["(None)", "(No Color)"])
                                continue
                            
                            is_constant = const_states[i] if i < len(const_states) else False
                            
                            if is_constant:
                                new_val = current_dds[i] if i < len(current_dds) else "(None)"
                                new_color = current_cols[i] if i < len(current_cols) else "(No Color)"
                            else:
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
                
                section_dd_color_outputs = []
                for i in range(len(dropdown_list)):
                    section_dd_color_outputs.extend([dropdown_list[i], color_list[i]])
                
                section_data["random_btn"].click(
                    fn=make_section_randomize(slots, constant_list, dropdown_list, color_list),
                    inputs=[palette_dropdown, color_mode] + constant_list + dropdown_list + color_list,
                    outputs=section_dd_color_outputs
                )
            
            # Per-slot random buttons
            for i, (btn_tuple, _) in enumerate(zip(all_random_btns, slot_names_list)):
                btn, slot_name = btn_tuple
                
                def make_slot_random(sn, idx):
                    def handler(palette_name, color_mode_val):
                        item = self.generator.sample_slot(sn)
                        new_val = item.get("name", "(None)") if item else "(None)"
                        
                        new_color = "(No Color)"
                        has_color = self.generator.SLOT_DEFINITIONS[sn].get("has_color", False)
                        if has_color:
                            palette_id = None
                            if color_mode_val == "Palette" and palette_name and palette_name != "(None)":
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
            for i, (btn_tuple, _) in enumerate(zip(all_color_btns, slot_names_list)):
                btn, slot_name = btn_tuple
                
                def make_color_random(sn):
                    def handler(palette_name, color_mode_val):
                        has_color = self.generator.SLOT_DEFINITIONS[sn].get("has_color", False)
                        if not has_color:
                            return "(No Color)"
                        
                        palette_id = None
                        if color_mode_val == "Palette" and palette_name and palette_name != "(None)":
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
                    fn=make_color_random(slot_name),
                    inputs=[palette_dropdown, color_mode],
                    outputs=[all_colors[i]]
                )
            
            # ===== SAVE/LOAD HANDLERS =====
            
            # Save config
            def save_config_handler(config_name, *slot_values):
                if not config_name or config_name.strip() == "":
                    return gr.update(value="❌ Please enter a configuration name")
                
                config = GeneratorConfig(name=config_name.strip())
                config.created_at = datetime.now().isoformat()
                
                num_slots = len(slot_names_list)
                # slot_values = enabled + dropdowns + colors + weights
                enabled_vals = slot_values[:num_slots]
                dropdown_vals = slot_values[num_slots:num_slots*2]
                color_vals = slot_values[num_slots*2:num_slots*3]
                weight_vals = slot_values[num_slots*3:]
                
                for i, slot_name in enumerate(slot_names_list):
                    slot_config = SlotConfig(
                        enabled=bool(enabled_vals[i]) if i < len(enabled_vals) else True,
                        value=dropdown_vals[i] if i < len(dropdown_vals) and dropdown_vals[i] != "(None)" else None,
                        color=color_vals[i] if i < len(color_vals) and color_vals[i] != "(No Color)" else None,
                        color_enabled=bool(color_vals[i] and color_vals[i] != "(No Color)") if i < len(color_vals) else False,
                        weight=float(weight_vals[i]) if i < len(weight_vals) and weight_vals[i] else 1.0
                    )
                    config.slots[slot_name] = slot_config
                
                filepath = self.configs_dir / f"{config_name.strip()}.json"
                self.generator.save_config(config, filepath)
                
                return gr.update(value=f"✅ Saved: {config_name}")
            
            save_btn.click(
                fn=save_config_handler,
                inputs=[config_name_input] + all_enabled + all_dropdowns + all_colors + all_weights,
                outputs=[save_status]
            )
            
            # Load config
            def load_config_handler(config_name):
                num_slots = len(slot_names_list)
                default_dropdowns = ["(None)"] * num_slots
                default_colors = ["(No Color)"] * num_slots
                default_weights = [1.0] * num_slots
                
                if not config_name:
                    return default_dropdowns + default_colors + default_weights + [gr.update(value="❌ Please select a config")]
                
                filepath = self.configs_dir / f"{config_name}.json"
                if not filepath.exists():
                    return default_dropdowns + default_colors + default_weights + [gr.update(value=f"❌ Config not found: {config_name}")]
                
                try:
                    config = self.generator.load_config(filepath)
                    dropdowns = []
                    colors = []
                    weights = []
                    
                    for slot_name in slot_names_list:
                        slot = config.slots.get(slot_name, SlotConfig())
                        dropdowns.append(slot.value or "(None)")
                        colors.append(slot.color or "(No Color)")
                        weights.append(slot.weight if slot.weight else 1.0)
                    
                    return dropdowns + colors + weights + [gr.update(value=f"✅ Loaded: {config_name}")]
                except Exception as e:
                    print(f"Error loading config: {e}")
                    return default_dropdowns + default_colors + default_weights + [gr.update(value=f"❌ Error: {str(e)}")]
            
            load_btn.click(
                fn=load_config_handler,
                inputs=[load_dropdown],
                outputs=all_dropdowns + all_colors + all_weights + [save_status]
            )
            
            # Refresh configs list
            def refresh_configs():
                configs = self.get_saved_configs()
                return gr.update(choices=configs, value=None)
            
            refresh_configs_btn.click(fn=refresh_configs, inputs=[], outputs=[load_dropdown])
            
            # Also refresh after saving
            save_btn.click(fn=refresh_configs, inputs=[], outputs=[load_dropdown])
            
            # Copy button - in Gradio 6.x we use js for clipboard
            copy_btn.click(
                fn=lambda x: x,
                inputs=[output_prompt],
                outputs=[output_prompt],
                js="(text) => { navigator.clipboard.writeText(text); return text; }"
            )
            
            # Shutdown button - cleanly stops server and releases port
            shutdown_btn.click(
                fn=shutdown_server,
                inputs=[],
                outputs=[]
            )
        
        return app


def create_app() -> gr.Blocks:
    """Create and return the Gradio app."""
    ui = PromptGeneratorUI()
    return ui.build_ui()


if __name__ == "__main__":
    app = create_app()
    app.launch()

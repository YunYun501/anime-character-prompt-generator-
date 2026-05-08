"""
ComfyUI node implementation for Random Character Prompt Generator.
"""

import random
import re
from pathlib import Path
from .prompt_generator import PromptGenerator, SlotConfig


class RandomCharacterPromptNode:
    """
    Generates random anime character prompts for Stable Diffusion.
    Outputs a prompt string that can be connected to CLIP Text Encode.
    """

    def __init__(self):
        self.gen = None
        self._palette_list = None

    def _ensure_generator(self):
        """Lazy-load the generator to avoid slow startup."""
        if self.gen is None:
            self.gen = PromptGenerator()
            self._palette_list = ["none"] + [p["id"] for p in self.gen.get_palette_list()]

    def _randomize_all_with_groups(self, config, include_color, palette_id, disabled_groups):
        """Randomize all slots, applying group filtering to clothing slots."""
        # Clothing slots that should respect group filtering
        clothing_slots = {"head", "neck", "upper_body", "waist", "lower_body",
                         "full_body", "outerwear", "hands", "legs", "feet", "accessory"}

        for slot_name in self.gen.SLOT_DEFINITIONS:
            if slot_name in config.slots and config.slots[slot_name].locked:
                continue

            slot = config.slots.get(slot_name)
            if not slot:
                from .prompt_generator import SlotConfig
                slot = SlotConfig()
                config.slots[slot_name] = slot

            # Apply group filtering only to clothing slots
            if slot_name in clothing_slots and disabled_groups:
                item = self.gen.sample_slot(slot_name, disabled_groups=disabled_groups)
            else:
                item = self.gen.sample_slot(slot_name)

            if item:
                slot.value = item.get("name", "")
                slot.value_id = item.get("id", "")
            else:
                slot.value = None
                slot.value_id = None

            # Handle color
            if include_color and self.gen.SLOT_DEFINITIONS[slot_name].get("has_color", False):
                if palette_id and palette_id in self.gen.palettes:
                    slot.color = self.gen.sample_color_from_palette(palette_id)
                    slot.color_enabled = True

        # Apply full_body logic
        if config.full_body_mode:
            self.gen._apply_full_body_logic(config)
        self.gen._apply_lower_body_leg_logic(config)

    # Clothing theme groups that can be enabled/disabled
    CLOTHING_GROUPS = [
        "uniform_service",
        "chinese_traditional",
        "japanese_traditional",
        "modern_everyday",
        "formal_fashion",
        "sports_stage",
        "armor_fantasy",
        "swimwear",
        "cute_themed",
        "props_tech",
    ]

    @classmethod
    def INPUT_TYPES(cls):
        """Define node inputs."""
        # We need to instantiate temporarily to get palette list
        temp_gen = PromptGenerator()
        palette_ids = ["none", "random"] + [p["id"] for p in temp_gen.get_palette_list()]

        return {
            "required": {
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "tooltip": "Random seed for reproducible results"
                }),
                "language": (["en", "zh"], {
                    "default": "en",
                    "tooltip": "Output language for prompt text"
                }),
                "palette": (palette_ids, {
                    "default": "none",
                    "tooltip": "Color palette for clothing items"
                }),
                "body_mode": (["normal", "full_body", "upper_body", "random"], {
                    "default": "normal",
                    "tooltip": "normal=all slots, full_body=skips upper/lower, upper_body=skips lower/legs/feet, random=pick one"
                }),
                # Clothing theme toggles
                "uniform_service": ("BOOLEAN", {"default": True, "tooltip": "Include uniforms, military, service outfits"}),
                "chinese_traditional": ("BOOLEAN", {"default": True, "tooltip": "Include Chinese traditional clothing"}),
                "japanese_traditional": ("BOOLEAN", {"default": True, "tooltip": "Include Japanese traditional clothing"}),
                "modern_everyday": ("BOOLEAN", {"default": True, "tooltip": "Include modern casual clothing"}),
                "formal_fashion": ("BOOLEAN", {"default": True, "tooltip": "Include formal and fashion clothing"}),
                "sports_stage": ("BOOLEAN", {"default": True, "tooltip": "Include sports and stage outfits"}),
                "armor_fantasy": ("BOOLEAN", {"default": True, "tooltip": "Include armor and fantasy outfits"}),
                "swimwear": ("BOOLEAN", {"default": True, "tooltip": "Include swimwear"}),
                "cute_themed": ("BOOLEAN", {"default": True, "tooltip": "Include cute and themed outfits"}),
                "props_tech": ("BOOLEAN", {"default": True, "tooltip": "Include props and tech accessories"}),
                # Slot enable/disable toggles
                "enable_head": ("BOOLEAN", {"default": False, "tooltip": "Include head accessories (hats, headbands, etc.)"}),
                "enable_eye_accessories": ("BOOLEAN", {"default": False, "tooltip": "Include eye accessories (glasses, eyepatch, etc.)"}),
                "enable_special_features": ("BOOLEAN", {"default": False, "tooltip": "Include special features (wings, horns, etc.)"}),
                "enable_hands": ("BOOLEAN", {"default": False, "tooltip": "Include hand accessories (gloves, etc.)"}),
                "enable_skin": ("BOOLEAN", {"default": True, "tooltip": "Include skin descriptions"}),
            },
            "optional": {
                "prefix": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Text to prepend to generated prompt (e.g., quality tags)"
                }),
                "lock_hair_color": ("STRING", {
                    "default": "",
                    "tooltip": "Lock hair color (e.g., 'blonde hair', 'pink hair')"
                }),
                "lock_eye_color": ("STRING", {
                    "default": "",
                    "tooltip": "Lock eye color (e.g., 'blue eyes', 'red eyes')"
                }),
                "lock_expression": ("STRING", {
                    "default": "",
                    "tooltip": "Lock expression (e.g., 'smile', 'serious')"
                }),
                "lock_body_type": ("STRING", {
                    "default": "",
                    "tooltip": "Lock body type (e.g., 'slim', 'curvy', 'muscular')"
                }),
                "lock_height": ("STRING", {
                    "default": "",
                    "tooltip": "Lock height (e.g., 'tall', 'short', 'average')"
                }),
                "lock_age_appearance": ("STRING", {
                    "default": "",
                    "tooltip": "Lock age appearance (e.g., 'young', 'mature', 'youthful')"
                }),
                "lock_background": ("STRING", {
                    "default": "",
                    "tooltip": "Lock background (e.g., 'outdoor', 'bedroom', 'simple background')"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    OUTPUT_NODE = True  # Allows showing output in UI
    FUNCTION = "generate"
    CATEGORY = "prompt"

    def generate(self, seed, language, palette, body_mode,
                 uniform_service=True, chinese_traditional=True, japanese_traditional=True,
                 modern_everyday=True, formal_fashion=True, sports_stage=True,
                 armor_fantasy=True, swimwear=True, cute_themed=True, props_tech=True,
                 enable_head=False, enable_eye_accessories=False, enable_special_features=False,
                 enable_hands=False, enable_skin=True,
                 prefix="", lock_hair_color="", lock_eye_color="",
                 lock_expression="", lock_body_type="", lock_height="", lock_age_appearance="",
                 lock_background=""):
        """Generate a random character prompt."""
        self._ensure_generator()

        # Set random seed for reproducibility
        random.seed(seed)

        # Resolve body mode (handle random)
        if body_mode == "random":
            actual_body_mode = random.choice(["normal", "full_body", "upper_body"])
        else:
            actual_body_mode = body_mode

        full_body_mode = (actual_body_mode == "full_body")
        upper_body_mode = (actual_body_mode == "upper_body")

        # Build disabled groups list from toggles
        disabled_groups = []
        group_toggles = {
            "uniform_service": uniform_service,
            "chinese_traditional": chinese_traditional,
            "japanese_traditional": japanese_traditional,
            "modern_everyday": modern_everyday,
            "formal_fashion": formal_fashion,
            "sports_stage": sports_stage,
            "armor_fantasy": armor_fantasy,
            "swimwear": swimwear,
            "cute_themed": cute_themed,
            "props_tech": props_tech,
        }
        for group_key, enabled in group_toggles.items():
            if not enabled:
                disabled_groups.append(group_key)

        # Create config and randomize
        config = self.gen.create_default_config()
        config.full_body_mode = full_body_mode

        # Determine palette
        if palette == "none":
            palette_id = None
        elif palette == "random":
            # Randomly select from available palettes
            available_palettes = list(self.gen.palettes.keys())
            palette_id = random.choice(available_palettes) if available_palettes else None
        else:
            palette_id = palette
        include_color = palette_id is not None

        # Randomize all slots with group filtering
        self._randomize_all_with_groups(config, include_color, palette_id, disabled_groups)

        # Apply upper body mode (disable lower body slots)
        if upper_body_mode:
            for slot_name in ["waist", "lower_body", "full_body", "legs", "feet"]:
                if slot_name in config.slots:
                    config.slots[slot_name].enabled = False

        # Apply slot enable/disable toggles
        slot_toggles = {
            "head": enable_head,
            "eye_accessories": enable_eye_accessories,
            "special_features": enable_special_features,
            "hands": enable_hands,
            "skin": enable_skin,
        }
        for slot_name, enabled in slot_toggles.items():
            if slot_name in config.slots:
                config.slots[slot_name].enabled = enabled

        # Apply locks (override randomized values)
        locks = {
            "hair_color": lock_hair_color,
            "eye_color": lock_eye_color,
            "expression": lock_expression,
            "body_type": lock_body_type,
            "height": lock_height,
            "age_appearance": lock_age_appearance,
            "background": lock_background,
        }

        for slot_name, locked_value in locks.items():
            if locked_value and locked_value.strip():
                if slot_name in config.slots:
                    config.slots[slot_name].value = locked_value.strip()
                    config.slots[slot_name].value_id = locked_value.strip()

        # Build the prompt with localization
        prompt = self._build_prompt_localized(config, language)

        # Add prefix if provided
        if prefix and prefix.strip():
            prompt = f"{prefix.strip()}, {prompt}"

        # Print to console for debugging
        print(f"\n{'='*50}")
        print(f"Generated Prompt")
        print(f"  Palette: {palette_id or 'none'}")
        print(f"  Body Mode: {actual_body_mode}")
        print(f"{'='*50}")
        print(prompt)
        print(f"{'='*50}\n")

        # Return prompt and display in UI
        return {"ui": {"text": [prompt]}, "result": (prompt,)}

    def _build_prompt_localized(self, config, language: str) -> str:
        """Build prompt with localized item names."""
        parts = ["1girl"]

        slot_order = [
            "hair_color", "hair_length", "hair_style", "hair_texture",
            "eye_color", "eye_expression_quality", "eye_shape", "eye_pupil_state",
            "eye_state", "eye_accessories",
            "body_type", "height", "skin", "age_appearance", "special_features",
            "expression",
            "full_body", "head", "neck", "upper_body", "waist", "lower_body",
            "outerwear", "hands", "legs", "feet", "accessory",
            "view_angle", "pose", "gesture",
            "background"
        ]

        # Check if lower body covers legs
        lower_body_covers_legs = False
        lower_slot = config.slots.get("lower_body")
        if lower_slot and lower_slot.enabled and lower_slot.value_id:
            lower_body_covers_legs = self.gen.lower_body_id_covers_legs(lower_slot.value_id)

        for slot_name in slot_order:
            if slot_name not in config.slots:
                continue

            slot = config.slots[slot_name]
            if not slot.enabled or not slot.value_id:
                continue

            # Full body mode logic
            if config.full_body_mode and slot_name in ["upper_body", "lower_body"]:
                full_body_slot = config.slots.get("full_body")
                if full_body_slot and full_body_slot.enabled and full_body_slot.value_id:
                    continue

            # Skip legs if lower body covers them
            if slot_name == "legs" and lower_body_covers_legs:
                continue

            # Get localized name
            localized_name = self.gen.resolve_slot_value_name(
                slot_name, slot.value_id, slot.value, language
            )
            if not localized_name:
                localized_name = slot.value or slot.value_id

            # Build prompt part with optional color
            if slot.color_enabled and slot.color:
                color_text = self.gen.localize_color_token(slot.color, language) or slot.color
                prompt_part = f"{color_text} {localized_name}"
            else:
                prompt_part = localized_name

            # Apply weight
            if slot.weight != 1.0:
                prompt_part = f"({prompt_part}:{slot.weight:.1f})"

            parts.append(prompt_part)

        return ", ".join(parts)


class ExpandedAutoPrompterNode:
    """
    Expanded Auto Prompter - uses the expanded tag library with 20,000+ items.

    This node uses action-verb-based classification to properly categorize tags
    like "grabbing own breast" and "skirt lift" as gestures rather than body/clothing.

    Features:
    - 20,000+ auto-generated tags from anime image databases
    - Smart action-verb classification (grab, press, lift, etc.)
    - Gesture categories: body_touch, clothing_adjust, object_interaction
    - Full bilingual support (English/Chinese)
    """

    def __init__(self):
        self.gen = None
        self._palette_list = None

    def _ensure_generator(self):
        """Lazy-load the generator in expanded mode."""
        if self.gen is None:
            self.gen = PromptGenerator(catalog_mode="expanded")
            self._palette_list = ["none", "random"] + [p["id"] for p in self.gen.get_palette_list()]
            print(f"[ExpandedAutoPrompter] Loaded {self.gen.get_total_items()} items in expanded mode")

    # Gesture groups from expanded catalogs
    GESTURE_GROUPS = [
        "gesture_body_touch",
        "gesture_clothing_adjust",
        "gesture_object_interaction",
        "gesture_general",
    ]

    # Clothing theme groups (same as lightweight)
    CLOTHING_GROUPS = [
        "uniform_service",
        "chinese_traditional",
        "japanese_traditional",
        "modern_everyday",
        "formal_fashion",
        "sports_stage",
        "armor_fantasy",
        "swimwear",
        "cute_themed",
        "props_tech",
    ]

    @classmethod
    def INPUT_TYPES(cls):
        """Define node inputs."""
        temp_gen = PromptGenerator(catalog_mode="expanded")
        palette_ids = ["none", "random"] + [p["id"] for p in temp_gen.get_palette_list()]

        return {
            "required": {
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "tooltip": "Random seed for reproducible results"
                }),
                "language": (["en", "zh"], {
                    "default": "en",
                    "tooltip": "Output language for prompt text"
                }),
                "palette": (palette_ids, {
                    "default": "none",
                    "tooltip": "Color palette for clothing items"
                }),
                "body_mode": (["normal", "full_body", "upper_body", "random"], {
                    "default": "random",
                    "tooltip": "Body framing mode"
                }),
                # Gesture toggles - the expanded catalog feature!
                "gesture_body_touch": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Include body touch gestures (grab, press, squeeze, etc.)"
                }),
                "gesture_clothing_adjust": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Include clothing adjustment gestures (lift, pull, adjust, etc.)"
                }),
                "gesture_object_interaction": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Include object interaction gestures (holding, carrying, etc.)"
                }),
                # Clothing theme toggles (same as lightweight)
                "uniform_service": ("BOOLEAN", {"default": True, "tooltip": "Include uniforms, military, service outfits"}),
                "chinese_traditional": ("BOOLEAN", {"default": True, "tooltip": "Include Chinese traditional clothing"}),
                "japanese_traditional": ("BOOLEAN", {"default": True, "tooltip": "Include Japanese traditional clothing"}),
                "modern_everyday": ("BOOLEAN", {"default": True, "tooltip": "Include modern casual clothing"}),
                "formal_fashion": ("BOOLEAN", {"default": True, "tooltip": "Include formal and fashion clothing"}),
                "sports_stage": ("BOOLEAN", {"default": True, "tooltip": "Include sports and stage outfits"}),
                "armor_fantasy": ("BOOLEAN", {"default": True, "tooltip": "Include armor and fantasy outfits"}),
                "swimwear": ("BOOLEAN", {"default": True, "tooltip": "Include swimwear"}),
                "cute_themed": ("BOOLEAN", {"default": True, "tooltip": "Include cute and themed outfits"}),
                "props_tech": ("BOOLEAN", {"default": True, "tooltip": "Include props and tech accessories"}),
                # Slot enable/disable toggles (same as lightweight)
                "enable_head": ("BOOLEAN", {"default": False, "tooltip": "Include head accessories (hats, headbands, etc.)"}),
                "enable_eye_accessories": ("BOOLEAN", {"default": False, "tooltip": "Include eye accessories (glasses, eyepatch, etc.)"}),
                "enable_special_features": ("BOOLEAN", {"default": False, "tooltip": "Include special features (wings, horns, etc.)"}),
                "enable_hands": ("BOOLEAN", {"default": False, "tooltip": "Include hand accessories (gloves, etc.)"}),
                "enable_skin": ("BOOLEAN", {"default": True, "tooltip": "Include skin descriptions"}),
            },
            "optional": {
                "prefix": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Text to prepend to generated prompt"
                }),
                "suffix": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Text to append to generated prompt"
                }),
                # Lock options (same as lightweight)
                "lock_hair_color": ("STRING", {
                    "default": "",
                    "tooltip": "Lock hair color (e.g., 'blonde hair', 'pink hair')"
                }),
                "lock_eye_color": ("STRING", {
                    "default": "",
                    "tooltip": "Lock eye color (e.g., 'blue eyes', 'red eyes')"
                }),
                "lock_expression": ("STRING", {
                    "default": "",
                    "tooltip": "Lock expression (e.g., 'smile', 'serious')"
                }),
                "lock_body_type": ("STRING", {
                    "default": "",
                    "tooltip": "Lock body type (e.g., 'slim', 'curvy', 'muscular')"
                }),
                "lock_height": ("STRING", {
                    "default": "",
                    "tooltip": "Lock height (e.g., 'tall', 'short', 'average')"
                }),
                "lock_age_appearance": ("STRING", {
                    "default": "",
                    "tooltip": "Lock age appearance (e.g., 'young', 'mature', 'youthful')"
                }),
                "lock_background": ("STRING", {
                    "default": "",
                    "tooltip": "Lock background (e.g., 'outdoor', 'bedroom', 'simple background')"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    OUTPUT_NODE = True
    FUNCTION = "generate"
    CATEGORY = "prompt"

    def generate(self, seed, language, palette, body_mode,
                 gesture_body_touch=True, gesture_clothing_adjust=True,
                 gesture_object_interaction=True,
                 uniform_service=True, chinese_traditional=True, japanese_traditional=True,
                 modern_everyday=True, formal_fashion=True, sports_stage=True,
                 armor_fantasy=True, swimwear=True, cute_themed=True, props_tech=True,
                 enable_head=False, enable_eye_accessories=False, enable_special_features=False,
                 enable_hands=False, enable_skin=True,
                 prefix="", suffix="",
                 lock_hair_color="", lock_eye_color="", lock_expression="",
                 lock_body_type="", lock_height="", lock_age_appearance="",
                 lock_background=""):
        """Generate a random character prompt using expanded catalogs."""
        self._ensure_generator()

        # Set random seed for reproducibility
        random.seed(seed)

        # Resolve body mode
        if body_mode == "random":
            actual_body_mode = random.choice(["normal", "full_body", "upper_body"])
        else:
            actual_body_mode = body_mode

        full_body_mode = (actual_body_mode == "full_body")
        upper_body_mode = (actual_body_mode == "upper_body")

        # Build disabled gesture groups
        disabled_gesture_groups = []
        if not gesture_body_touch:
            disabled_gesture_groups.append("gesture_body_touch")
        if not gesture_clothing_adjust:
            disabled_gesture_groups.append("gesture_clothing_adjust")
        if not gesture_object_interaction:
            disabled_gesture_groups.append("gesture_object_interaction")

        # Build disabled clothing groups (same as lightweight)
        disabled_clothing_groups = []
        group_toggles = {
            "uniform_service": uniform_service,
            "chinese_traditional": chinese_traditional,
            "japanese_traditional": japanese_traditional,
            "modern_everyday": modern_everyday,
            "formal_fashion": formal_fashion,
            "sports_stage": sports_stage,
            "armor_fantasy": armor_fantasy,
            "swimwear": swimwear,
            "cute_themed": cute_themed,
            "props_tech": props_tech,
        }
        for group_key, enabled in group_toggles.items():
            if not enabled:
                disabled_clothing_groups.append(group_key)

        # Create config
        config = self.gen.create_default_config()
        config.full_body_mode = full_body_mode

        # Determine palette
        if palette == "none":
            palette_id = None
        elif palette == "random":
            available_palettes = list(self.gen.palettes.keys())
            palette_id = random.choice(available_palettes) if available_palettes else None
        else:
            palette_id = palette
        include_color = palette_id is not None

        # Clothing slots that should respect group filtering
        clothing_slots = {"head", "neck", "upper_body", "waist", "lower_body",
                         "full_body", "outerwear", "hands", "legs", "feet", "accessory"}

        # Randomize all slots
        for slot_name in self.gen.SLOT_DEFINITIONS:
            if slot_name in config.slots and config.slots[slot_name].locked:
                continue

            slot = config.slots.get(slot_name)
            if not slot:
                slot = SlotConfig()
                config.slots[slot_name] = slot

            # Apply gesture group filtering for gesture slot
            if slot_name == "gesture" and disabled_gesture_groups:
                item = self.gen.sample_slot(slot_name, disabled_groups=disabled_gesture_groups)
            # Apply clothing group filtering for clothing slots
            elif slot_name in clothing_slots and disabled_clothing_groups:
                item = self.gen.sample_slot(slot_name, disabled_groups=disabled_clothing_groups)
            else:
                item = self.gen.sample_slot(slot_name)

            if item:
                slot.value = item.get("name", "")
                slot.value_id = item.get("id", "")
            else:
                slot.value = None
                slot.value_id = None

            # Handle color
            if include_color and self.gen.SLOT_DEFINITIONS[slot_name].get("has_color", False):
                if palette_id and palette_id in self.gen.palettes:
                    slot.color = self.gen.sample_color_from_palette(palette_id)
                    slot.color_enabled = True

        # Apply full_body logic
        if config.full_body_mode:
            self.gen._apply_full_body_logic(config)
        self.gen._apply_lower_body_leg_logic(config)

        # Apply upper body mode
        if upper_body_mode:
            for slot_name in ["waist", "lower_body", "full_body", "legs", "feet"]:
                if slot_name in config.slots:
                    config.slots[slot_name].enabled = False

        # Apply slot enable/disable toggles (same as lightweight)
        slot_toggles = {
            "head": enable_head,
            "eye_accessories": enable_eye_accessories,
            "special_features": enable_special_features,
            "hands": enable_hands,
            "skin": enable_skin,
        }
        for slot_name, enabled in slot_toggles.items():
            if slot_name in config.slots:
                config.slots[slot_name].enabled = enabled

        # Apply locks (same as lightweight)
        locks = {
            "hair_color": lock_hair_color,
            "eye_color": lock_eye_color,
            "expression": lock_expression,
            "body_type": lock_body_type,
            "height": lock_height,
            "age_appearance": lock_age_appearance,
            "background": lock_background,
        }

        for slot_name, locked_value in locks.items():
            if locked_value and locked_value.strip():
                if slot_name in config.slots:
                    config.slots[slot_name].value = locked_value.strip()
                    config.slots[slot_name].value_id = locked_value.strip()

        # Build prompt
        prompt = self._build_prompt_localized(config, language)

        # Add prefix/suffix
        if prefix and prefix.strip():
            prompt = f"{prefix.strip()}, {prompt}"
        if suffix and suffix.strip():
            prompt = f"{prompt}, {suffix.strip()}"

        # Print to console
        print(f"\n{'='*60}")
        print(f"[ExpandedAutoPrompter] Generated Prompt")
        print(f"  Mode: {actual_body_mode} | Palette: {palette_id or 'none'}")
        print(f"  Total items available: {self.gen.get_total_items()}")
        print(f"{'='*60}")
        print(prompt)
        print(f"{'='*60}\n")

        return {"ui": {"text": [prompt]}, "result": (prompt,)}

    def _build_prompt_localized(self, config, language: str) -> str:
        """Build prompt with localized item names."""
        parts = ["1girl"]

        slot_order = [
            "hair_color", "hair_length", "hair_style", "hair_texture",
            "eye_color", "eye_expression_quality", "eye_shape", "eye_pupil_state",
            "eye_state", "eye_accessories",
            "body_type", "height", "skin", "age_appearance", "special_features",
            "expression",
            "full_body", "head", "neck", "upper_body", "waist", "lower_body",
            "outerwear", "hands", "legs", "feet", "accessory",
            "view_angle", "pose", "gesture",
            "background"
        ]

        # Check if lower body covers legs
        lower_body_covers_legs = False
        lower_slot = config.slots.get("lower_body")
        if lower_slot and lower_slot.enabled and lower_slot.value_id:
            lower_body_covers_legs = self.gen.lower_body_id_covers_legs(lower_slot.value_id)

        for slot_name in slot_order:
            if slot_name not in config.slots:
                continue

            slot = config.slots[slot_name]
            if not slot.enabled or not slot.value_id:
                continue

            # Full body mode logic
            if config.full_body_mode and slot_name in ["upper_body", "lower_body"]:
                full_body_slot = config.slots.get("full_body")
                if full_body_slot and full_body_slot.enabled and full_body_slot.value_id:
                    continue

            # Skip legs if lower body covers them
            if slot_name == "legs" and lower_body_covers_legs:
                continue

            # Get localized name
            localized_name = self.gen.resolve_slot_value_name(
                slot_name, slot.value_id, slot.value, language
            )
            if not localized_name:
                localized_name = slot.value or slot.value_id

            # Build prompt part with optional color
            if slot.color_enabled and slot.color:
                color_text = self.gen.localize_color_token(slot.color, language) or slot.color
                prompt_part = f"{color_text} {localized_name}"
            else:
                prompt_part = localized_name

            # Apply weight
            if slot.weight != 1.0:
                prompt_part = f"({prompt_part}:{slot.weight:.1f})"

            parts.append(prompt_part)

        return ", ".join(parts)


class AutoPromptExpandedNode:
    """
    Auto Prompt Expanded (Constrained) - expanded catalog with constraint engine.

    Uses the cleaned expanded tag library with 16,513 items and applies logical
    consistency rules (e.g., helmet hides hair, closed eyes can't sparkle).

    Features:
    - Cleaned expanded catalogs (16,513 items post-filtering)
    - Constraint engine for logical consistency
    - Catalog stats display on generation
    - All gesture/clothing group toggles from ExpandedAutoPrompter
    """

    def __init__(self):
        self.gen = None
        self._palette_list = None

    def _ensure_generator(self):
        if self.gen is None:
            self.gen = PromptGenerator(catalog_mode="expanded")
            self._palette_list = ["none", "random"] + [p["id"] for p in self.gen.get_palette_list()]
            total = self.gen.get_total_items()
            print(f"[AutoPromptExpanded] Loaded {total} cleaned expanded items")

    GESTURE_GROUPS = [
        "gesture_body_touch",
        "gesture_clothing_adjust",
        "gesture_object_interaction",
        "gesture_general",
    ]

    CLOTHING_GROUPS = [
        "uniform_service",
        "chinese_traditional",
        "japanese_traditional",
        "modern_everyday",
        "formal_fashion",
        "sports_stage",
        "armor_fantasy",
        "swimwear",
        "cute_themed",
        "props_tech",
    ]

    # Tier 2 suggestive terms — used when sfw_strict is enabled
    SFW_BLOCKED_TERMS = {
        "panties", "panty", "underwear", "lingerie", "thong", "g-string",
        "bra", "brassiere", "bralette", "corset", "bustier", "garter belt",
        "cowgirl", "missionary", "doggystyle", "doggy style", "spread legs",
        "ass focus", "breast focus", "cameltoe", "camel toe", "upskirt",
        "downblouse", "underboob", "sideboob", "cleavage",
        "groping", "grope", "breast grab", "ass grab", "fondling", "fondle",
        "aroused", "erect", "erection", "seductive", "lewd", "ecchi", "hentai",
        "see through", "nude beach", "naked", "nude",
        "after sex", "post-coital", "post coital",
    }

    def _is_item_sfw_blocked(self, item):
        """Check if an item matches any Tier 2 suggestive term using word boundaries."""
        if not item:
            return False
        name = item.get("name", "").lower()
        for term in self.SFW_BLOCKED_TERMS:
            escaped = re.escape(term.lower())
            if re.search(r'\b' + escaped + r'\b', name):
                return True
        return False

    @classmethod
    def INPUT_TYPES(cls):
        temp_gen = PromptGenerator(catalog_mode="expanded")
        palette_ids = ["none", "random"] + [p["id"] for p in temp_gen.get_palette_list()]

        return {
            "required": {
                "seed": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "tooltip": "Random seed for reproducible results"
                }),
                "language": (["en", "zh"], {
                    "default": "en",
                    "tooltip": "Output language for prompt text"
                }),
                "palette": (palette_ids, {
                    "default": "none",
                    "tooltip": "Color palette for clothing items"
                }),
                "body_mode": (["normal", "full_body", "upper_body", "random"], {
                    "default": "random",
                    "tooltip": "Body framing mode"
                }),
                "use_constraints": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Apply logical consistency rules (e.g., helmet hides hair)"
                }),
                # Gesture toggles
                "gesture_body_touch": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Include body touch gestures (grab, press, squeeze, etc.)"
                }),
                "gesture_clothing_adjust": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Include clothing adjustment gestures (lift, pull, adjust, etc.)"
                }),
                "gesture_object_interaction": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "Include object interaction gestures (holding, carrying, etc.)"
                }),
                # Clothing theme toggles
                "uniform_service": ("BOOLEAN", {"default": True, "tooltip": "Include uniforms, military, service outfits"}),
                "chinese_traditional": ("BOOLEAN", {"default": True, "tooltip": "Include Chinese traditional clothing"}),
                "japanese_traditional": ("BOOLEAN", {"default": True, "tooltip": "Include Japanese traditional clothing"}),
                "modern_everyday": ("BOOLEAN", {"default": True, "tooltip": "Include modern casual clothing"}),
                "formal_fashion": ("BOOLEAN", {"default": True, "tooltip": "Include formal and fashion clothing"}),
                "sports_stage": ("BOOLEAN", {"default": True, "tooltip": "Include sports and stage outfits"}),
                "armor_fantasy": ("BOOLEAN", {"default": True, "tooltip": "Include armor and fantasy outfits"}),
                "swimwear": ("BOOLEAN", {"default": True, "tooltip": "Include swimwear"}),
                "cute_themed": ("BOOLEAN", {"default": True, "tooltip": "Include cute and themed outfits"}),
                "props_tech": ("BOOLEAN", {"default": True, "tooltip": "Include props and tech accessories"}),
                # Slot enable/disable toggles
                "enable_head": ("BOOLEAN", {"default": False, "tooltip": "Include head accessories (hats, headbands, etc.)"}),
                "enable_eye_accessories": ("BOOLEAN", {"default": False, "tooltip": "Include eye accessories (glasses, eyepatch, etc.)"}),
                "enable_special_features": ("BOOLEAN", {"default": False, "tooltip": "Include special features (wings, horns, etc.)"}),
                "enable_hands": ("BOOLEAN", {"default": False, "tooltip": "Include hand accessories (gloves, etc.)"}),
                "enable_skin": ("BOOLEAN", {"default": True, "tooltip": "Include skin descriptions"}),
                "sfw_strict": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "Remove suggestive content: intimate apparel, groping, sexual positions, etc."
                }),
            },
            "optional": {
                "prefix": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Text to prepend to generated prompt"
                }),
                "suffix": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "Text to append to generated prompt"
                }),
                "lock_hair_color": ("STRING", {
                    "default": "",
                    "tooltip": "Lock hair color (e.g., 'blonde hair', 'pink hair')"
                }),
                "lock_eye_color": ("STRING", {
                    "default": "",
                    "tooltip": "Lock eye color (e.g., 'blue eyes', 'red eyes')"
                }),
                "lock_expression": ("STRING", {
                    "default": "",
                    "tooltip": "Lock expression (e.g., 'smile', 'serious')"
                }),
                "lock_body_type": ("STRING", {
                    "default": "",
                    "tooltip": "Lock body type (e.g., 'slim', 'curvy', 'muscular')"
                }),
                "lock_height": ("STRING", {
                    "default": "",
                    "tooltip": "Lock height (e.g., 'tall', 'short', 'average')"
                }),
                "lock_age_appearance": ("STRING", {
                    "default": "",
                    "tooltip": "Lock age appearance (e.g., 'young', 'mature', 'youthful')"
                }),
                "lock_background": ("STRING", {
                    "default": "",
                    "tooltip": "Lock background (e.g., 'outdoor', 'bedroom', 'simple background')"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("prompt",)
    OUTPUT_NODE = True
    FUNCTION = "generate"
    CATEGORY = "prompt"

    def generate(self, seed, language, palette, body_mode, use_constraints,
                 sfw_strict=False,
                 gesture_body_touch=True, gesture_clothing_adjust=True,
                 gesture_object_interaction=True,
                 uniform_service=True, chinese_traditional=True, japanese_traditional=True,
                 modern_everyday=True, formal_fashion=True, sports_stage=True,
                 armor_fantasy=True, swimwear=True, cute_themed=True, props_tech=True,
                 enable_head=False, enable_eye_accessories=False, enable_special_features=False,
                 enable_hands=False, enable_skin=True,
                 prefix="", suffix="",
                 lock_hair_color="", lock_eye_color="", lock_expression="",
                 lock_body_type="", lock_height="", lock_age_appearance="",
                 lock_background=""):
        self._ensure_generator()

        random.seed(seed)

        if body_mode == "random":
            actual_body_mode = random.choice(["normal", "full_body", "upper_body"])
        else:
            actual_body_mode = body_mode

        full_body_mode = (actual_body_mode == "full_body")
        upper_body_mode = (actual_body_mode == "upper_body")

        disabled_gesture_groups = []
        if not gesture_body_touch:
            disabled_gesture_groups.append("gesture_body_touch")
        if not gesture_clothing_adjust:
            disabled_gesture_groups.append("gesture_clothing_adjust")
        if not gesture_object_interaction:
            disabled_gesture_groups.append("gesture_object_interaction")

        disabled_clothing_groups = []
        group_toggles = {
            "uniform_service": uniform_service,
            "chinese_traditional": chinese_traditional,
            "japanese_traditional": japanese_traditional,
            "modern_everyday": modern_everyday,
            "formal_fashion": formal_fashion,
            "sports_stage": sports_stage,
            "armor_fantasy": armor_fantasy,
            "swimwear": swimwear,
            "cute_themed": cute_themed,
            "props_tech": props_tech,
        }
        for group_key, enabled in group_toggles.items():
            if not enabled:
                disabled_clothing_groups.append(group_key)

        config = self.gen.create_default_config()
        config.full_body_mode = full_body_mode

        if palette == "none":
            palette_id = None
        elif palette == "random":
            available_palettes = list(self.gen.palettes.keys())
            palette_id = random.choice(available_palettes) if available_palettes else None
        else:
            palette_id = palette
        include_color = palette_id is not None

        clothing_slots = {"head", "neck", "upper_body", "waist", "lower_body",
                         "full_body", "outerwear", "hands", "legs", "feet", "accessory"}

        for slot_name in self.gen.SLOT_DEFINITIONS:
            if slot_name in config.slots and config.slots[slot_name].locked:
                continue

            slot = config.slots.get(slot_name)
            if not slot:
                slot = SlotConfig()
                config.slots[slot_name] = slot

            # Build disabled values from SFW filter
            sfw_blocked_ids = []
            if sfw_strict:
                options = self.gen.get_slot_options(slot_name)
                for opt in options:
                    if self._is_item_sfw_blocked(opt):
                        sfw_blocked_ids.append(opt.get("id"))

            if slot_name == "gesture" and disabled_gesture_groups:
                item = self.gen.sample_slot(slot_name,
                    disabled_groups=disabled_gesture_groups,
                    disabled_values=sfw_blocked_ids if sfw_blocked_ids else None)
            elif slot_name in clothing_slots and (disabled_clothing_groups or sfw_blocked_ids):
                item = self.gen.sample_slot(slot_name,
                    disabled_groups=disabled_clothing_groups if disabled_clothing_groups else None,
                    disabled_values=sfw_blocked_ids if sfw_blocked_ids else None)
            elif sfw_blocked_ids:
                item = self.gen.sample_slot(slot_name,
                    disabled_values=sfw_blocked_ids)
            else:
                item = self.gen.sample_slot(slot_name)

            if item:
                slot.value = item.get("name", "")
                slot.value_id = item.get("id", "")
            else:
                slot.value = None
                slot.value_id = None

            if include_color and self.gen.SLOT_DEFINITIONS[slot_name].get("has_color", False):
                if palette_id and palette_id in self.gen.palettes:
                    slot.color = self.gen.sample_color_from_palette(palette_id)
                    slot.color_enabled = True

        if config.full_body_mode:
            self.gen._apply_full_body_logic(config)
        self.gen._apply_lower_body_leg_logic(config)

        if upper_body_mode:
            for slot_name in ["waist", "lower_body", "full_body", "legs", "feet"]:
                if slot_name in config.slots:
                    config.slots[slot_name].enabled = False

        slot_toggles = {
            "head": enable_head,
            "eye_accessories": enable_eye_accessories,
            "special_features": enable_special_features,
            "hands": enable_hands,
            "skin": enable_skin,
        }
        for slot_name, enabled in slot_toggles.items():
            if slot_name in config.slots:
                config.slots[slot_name].enabled = enabled

        locks = {
            "hair_color": lock_hair_color,
            "eye_color": lock_eye_color,
            "expression": lock_expression,
            "body_type": lock_body_type,
            "height": lock_height,
            "age_appearance": lock_age_appearance,
            "background": lock_background,
        }
        for slot_name, locked_value in locks.items():
            if locked_value and locked_value.strip():
                if slot_name in config.slots:
                    config.slots[slot_name].value = locked_value.strip()
                    config.slots[slot_name].value_id = locked_value.strip()

        # Apply constraint engine for logical consistency
        constraints_applied = False
        if use_constraints:
            self.gen._apply_constraints(config)
            constraints_applied = True

        prompt = self._build_prompt_localized(config, language)

        if prefix and prefix.strip():
            prompt = f"{prefix.strip()}, {prompt}"
        if suffix and suffix.strip():
            prompt = f"{prompt}, {suffix.strip()}"

        # Console output with stats
        stats = self.gen.get_catalog_stats()
        stats_str = ", ".join(f"{k}={v}" for k, v in sorted(stats.items()))
        print(f"\n{'='*60}")
        print(f"[AutoPromptExpanded] Generated Prompt")
        print(f"  Mode: {actual_body_mode} | Palette: {palette_id or 'none'}")
        print(f"  Catalog stats: {stats_str}")
        print(f"  Constraints applied: {'yes' if constraints_applied else 'no'}")
        print(f"  SFW strict: {'yes' if sfw_strict else 'no'}")
        print(f"{'='*60}")
        print(prompt)
        print(f"{'='*60}\n")

        return {"ui": {"text": [prompt]}, "result": (prompt,)}

    def _build_prompt_localized(self, config, language: str) -> str:
        parts = ["1girl"]

        slot_order = [
            "hair_color", "hair_length", "hair_style", "hair_texture",
            "eye_color", "eye_expression_quality", "eye_shape", "eye_pupil_state",
            "eye_state", "eye_accessories",
            "body_type", "height", "skin", "age_appearance", "special_features",
            "expression",
            "full_body", "head", "neck", "upper_body", "waist", "lower_body",
            "outerwear", "hands", "legs", "feet", "accessory",
            "view_angle", "pose", "gesture",
            "background"
        ]

        lower_body_covers_legs = False
        lower_slot = config.slots.get("lower_body")
        if lower_slot and lower_slot.enabled and lower_slot.value_id:
            lower_body_covers_legs = self.gen.lower_body_id_covers_legs(lower_slot.value_id)

        for slot_name in slot_order:
            if slot_name not in config.slots:
                continue

            slot = config.slots[slot_name]
            if not slot.enabled or not slot.value_id:
                continue

            if config.full_body_mode and slot_name in ["upper_body", "lower_body"]:
                full_body_slot = config.slots.get("full_body")
                if full_body_slot and full_body_slot.enabled and full_body_slot.value_id:
                    continue

            if slot_name == "legs" and lower_body_covers_legs:
                continue

            localized_name = self.gen.resolve_slot_value_name(
                slot_name, slot.value_id, slot.value, language
            )
            if not localized_name:
                localized_name = slot.value or slot.value_id

            if slot.color_enabled and slot.color:
                color_text = self.gen.localize_color_token(slot.color, language) or slot.color
                prompt_part = f"{color_text} {localized_name}"
            else:
                prompt_part = localized_name

            if slot.weight != 1.0:
                prompt_part = f"({prompt_part}:{slot.weight:.1f})"

            parts.append(prompt_part)

        return ", ".join(parts)

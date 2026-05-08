"""
Core prompt generator logic for Random Character Prompt Generator.
Handles loading catalogs, random sampling, color palettes, and prompt building.

This is a self-contained copy for ComfyUI node usage.
Data folder should be at: auto_prompt/prompt data/
"""

import json
import random
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime


@dataclass
class SlotConfig:
    """Configuration for a single slot (e.g., upper_body, hair_color)."""
    enabled: bool = True
    locked: bool = False  # If locked, won't be changed by "Randomize All"
    value: Optional[str] = None  # Current selected item name
    value_id: Optional[str] = None  # Current selected item ID
    color: Optional[str] = None  # Color modifier (if applicable)
    color_enabled: bool = False  # Whether to include color in output
    weight: float = 1.0  # Prompt weight (1.0 = default, no weight syntax)

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "locked": self.locked,
            "value": self.value,
            "value_id": self.value_id,
            "color": self.color,
            "color_enabled": self.color_enabled,
            "weight": self.weight
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SlotConfig":
        return cls(**data)


@dataclass
class GeneratorConfig:
    """Overall generator configuration."""
    # Slot configurations by slot name
    slots: Dict[str, SlotConfig] = field(default_factory=dict)

    # Color mode: "none", "palette", "random"
    color_mode: str = "none"
    active_palette_id: Optional[str] = None

    # Full body mode toggle
    full_body_mode: bool = True  # When True, full_body disables upper/lower

    # Metadata
    name: str = "Untitled"
    created_at: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "created_at": self.created_at or datetime.now().isoformat(),
            "color_mode": self.color_mode,
            "active_palette_id": self.active_palette_id,
            "full_body_mode": self.full_body_mode,
            "slots": {k: v.to_dict() for k, v in self.slots.items()}
        }

    @classmethod
    def from_dict(cls, data: dict) -> "GeneratorConfig":
        config = cls(
            name=data.get("name", "Untitled"),
            created_at=data.get("created_at"),
            color_mode=data.get("color_mode", "none"),
            active_palette_id=data.get("active_palette_id"),
            full_body_mode=data.get("full_body_mode", True)
        )
        for slot_name, slot_data in data.get("slots", {}).items():
            config.slots[slot_name] = SlotConfig.from_dict(slot_data)
        return config


class PromptGenerator:
    """Main prompt generator class."""
    DEFAULT_DATA_DIRNAME = "prompt data"
    SUPPORTED_LANGUAGES = ("en", "zh")
    CATALOG_MODES = ("lightweight", "expanded")

    # Define all available slots and their categories
    SLOT_DEFINITIONS = {
        # Appearance
        "hair_style": {"category": "appearance", "catalog": "hair", "index_key": "style", "has_color": False},
        "hair_length": {"category": "appearance", "catalog": "hair", "index_key": "length", "has_color": False},
        "hair_color": {"category": "appearance", "catalog": "hair", "index_key": "color", "has_color": False},
        "hair_texture": {"category": "appearance", "catalog": "hair", "index_key": "texture", "has_color": False},
        "eye_color": {"category": "appearance", "catalog": "eyes", "index_key": "color", "has_color": False},
        "eye_expression_quality": {"category": "appearance", "catalog": "eyes", "index_key": "expression_quality", "has_color": False},
        "eye_shape": {"category": "appearance", "catalog": "eyes", "index_key": "eye_shape", "has_color": False},
        "eye_pupil_state": {"category": "appearance", "catalog": "eyes", "index_key": "pupil_state", "has_color": False},
        "eye_state": {"category": "appearance", "catalog": "eyes", "index_key": "eye_state", "has_color": False},
        "eye_accessories": {"category": "appearance", "catalog": "eyes", "index_key": "eye_accessories", "has_color": False},

        # Body
        "body_type": {"category": "body", "catalog": "body", "index_key": "body_type", "has_color": False},
        "height": {"category": "body", "catalog": "body", "index_key": "height", "has_color": False},
        "skin": {"category": "body", "catalog": "body", "index_key": "skin", "has_color": False},
        "age_appearance": {"category": "body", "catalog": "body", "index_key": "age_appearance", "has_color": False},
        "special_features": {"category": "body", "catalog": "body", "index_key": "special_features", "has_color": False},

        # Expression
        "expression": {"category": "expression", "catalog": "expressions", "index_key": None, "has_color": False},

        # Clothing
        "head": {"category": "clothing", "catalog": "clothing", "index_key": "head", "has_color": True},
        "neck": {"category": "clothing", "catalog": "clothing", "index_key": "neck", "has_color": True},
        "upper_body": {"category": "clothing", "catalog": "clothing", "index_key": "upper_body", "has_color": True},
        "waist": {"category": "clothing", "catalog": "clothing", "index_key": "waist", "has_color": True},
        "lower_body": {"category": "clothing", "catalog": "clothing", "index_key": "lower_body", "has_color": True},
        "full_body": {"category": "clothing", "catalog": "clothing", "index_key": "full_body", "has_color": True},
        "outerwear": {"category": "clothing", "catalog": "clothing", "index_key": "outerwear", "has_color": True},
        "hands": {"category": "clothing", "catalog": "clothing", "index_key": "hands", "has_color": True},
        "legs": {"category": "clothing", "catalog": "clothing", "index_key": "legs", "has_color": True},
        "feet": {"category": "clothing", "catalog": "clothing", "index_key": "feet", "has_color": True},
        "accessory": {"category": "clothing", "catalog": "clothing", "index_key": "accessory", "has_color": True},

        # Pose
        "pose": {"category": "pose", "catalog": "poses", "index_key": None, "has_color": False},
        "gesture": {"category": "pose", "catalog": "poses", "index_key": "gesture", "has_color": False},
        "view_angle": {"category": "pose", "catalog": "view_angles", "index_key": None, "has_color": False},

        # Background
        "background": {"category": "background", "catalog": "backgrounds", "index_key": None, "has_color": False},
    }

    # Categories for section-based randomization
    CATEGORIES = ["appearance", "body", "expression", "clothing", "pose", "background"]

    def __init__(self, data_dir: Optional[Path] = None, catalog_mode: str = "lightweight"):
        """Initialize the generator with data directory and catalog mode.

        Args:
            data_dir: Path to prompt data directory.
            catalog_mode: "lightweight" (curated only) or "expanded" (includes auto-generated).
        """
        if data_dir is None:
            # Default to 'prompt data' folder in the same directory as this file
            data_dir = Path(__file__).parent / self.DEFAULT_DATA_DIRNAME
        self.data_dir = Path(data_dir)

        # Catalog mode
        if catalog_mode not in self.CATALOG_MODES:
            catalog_mode = "lightweight"
        self.catalog_mode = catalog_mode

        # Loaded catalogs
        self.catalogs: Dict[str, dict] = {}

        # Color palettes
        self.palettes: Dict[str, dict] = {}
        self.individual_colors: List[str] = []

        # Item lookup maps (catalog -> id -> item)
        self.items_by_id: Dict[str, Dict[str, dict]] = {}
        # Reverse lookup maps (catalog -> lower(name) -> id)
        self.item_id_by_name: Dict[str, Dict[str, str]] = {}
        # Color token localization map (color -> {lang: localized_text})
        self.color_i18n: Dict[str, Dict[str, str]] = {}

        # Load all data
        self._load_catalogs()

    def _load_catalogs(self):
        """Load all catalog JSON files."""
        # Base (lightweight) catalog paths
        catalog_paths = {
            "clothing": self.data_dir / "clothing" / "clothing_list.json",
            "expressions": self.data_dir / "expressions" / "female_expressions.json",
            "hair": self.data_dir / "hair" / "hair_catalog.json",
            "eyes": self.data_dir / "eyes" / "eye_catalog.json",
            "body": self.data_dir / "body" / "body_features.json",
            "poses": self.data_dir / "poses" / "poses.json",
            "view_angles": self.data_dir / "view_angles" / "view_angles.json",
            "backgrounds": self.data_dir / "backgrounds" / "backgrounds.json",
            "colors": self.data_dir / "colors" / "color_palettes.json",
        }

        # Expanded catalog paths (only loaded in expanded mode)
        expanded_paths = {
            "clothing": self.data_dir / "clothing" / "clothing_expanded.json",
            "expressions": self.data_dir / "expressions" / "expressions_expanded.json",
            "hair": self.data_dir / "hair" / "hair_expanded.json",
            "eyes": self.data_dir / "eyes" / "eyes_expanded.json",
            "body": self.data_dir / "body" / "body_expanded.json",
            "poses": self.data_dir / "poses" / "poses_expanded.json",
            "view_angles": self.data_dir / "view_angles" / "view_angles_expanded.json",
            "backgrounds": self.data_dir / "backgrounds" / "backgrounds_expanded.json",
        }

        for name, path in catalog_paths.items():
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.catalogs[name] = data

                    # Build item lookup
                    if "items" in data:
                        self.items_by_id[name] = {
                            item["id"]: item for item in data["items"]
                        }
                        self.item_id_by_name[name] = {}
                        for item in data["items"]:
                            label = item.get("name")
                            if isinstance(label, str) and label:
                                self.item_id_by_name[name][label.strip().lower()] = item["id"]

                    # Special handling for colors
                    if name == "colors":
                        self.palettes = {
                            p["id"]: p for p in data.get("palettes", [])
                        }
                        self.individual_colors = data.get("individual_colors", [])
                        self.color_i18n = data.get("individual_colors_i18n", {})

        # Load expanded catalogs if in expanded mode
        if self.catalog_mode == "expanded":
            self._merge_expanded_catalogs(expanded_paths)

    def _merge_expanded_catalogs(self, expanded_paths: Dict[str, Path]) -> None:
        """Merge expanded catalog items into base catalogs."""
        for name, path in expanded_paths.items():
            if not path.exists():
                continue

            with open(path, "r", encoding="utf-8") as f:
                expanded_data = json.load(f)

            if "items" not in expanded_data:
                continue

            # Get existing IDs to avoid duplicates
            existing_ids = set(self.items_by_id.get(name, {}).keys())

            # Add new items from expanded catalog
            new_items = []
            for item in expanded_data["items"]:
                item_id = item.get("id")
                if item_id and item_id not in existing_ids:
                    new_items.append(item)
                    existing_ids.add(item_id)

            if not new_items:
                continue

            # Merge into catalog
            if name not in self.catalogs:
                self.catalogs[name] = {"items": []}
            if "items" not in self.catalogs[name]:
                self.catalogs[name]["items"] = []

            self.catalogs[name]["items"].extend(new_items)

            # Update lookup maps
            if name not in self.items_by_id:
                self.items_by_id[name] = {}
            if name not in self.item_id_by_name:
                self.item_id_by_name[name] = {}

            for item in new_items:
                item_id = item.get("id")
                if item_id:
                    self.items_by_id[name][item_id] = item
                label = item.get("name")
                if isinstance(label, str) and label:
                    self.item_id_by_name[name][label.strip().lower()] = item_id

            # Merge index_by_category if present
            if "index_by_category" in expanded_data and "index_by_category" in self.catalogs[name]:
                for category, ids in expanded_data["index_by_category"].items():
                    if category not in self.catalogs[name]["index_by_category"]:
                        self.catalogs[name]["index_by_category"][category] = []
                    for item_id in ids:
                        if item_id not in self.catalogs[name]["index_by_category"][category]:
                            self.catalogs[name]["index_by_category"][category].append(item_id)

            # Merge index_by_body_part for clothing catalog
            if name == "clothing":
                if "index_by_body_part" not in self.catalogs[name]:
                    self.catalogs[name]["index_by_body_part"] = {}
                for item in new_items:
                    item_id = item.get("id")
                    group = item.get("group")  # e.g., "full_body", "upper_body", "head"
                    if item_id and group:
                        if group not in self.catalogs[name]["index_by_body_part"]:
                            self.catalogs[name]["index_by_body_part"][group] = []
                        if item_id not in self.catalogs[name]["index_by_body_part"][group]:
                            self.catalogs[name]["index_by_body_part"][group].append(item_id)

            # Merge group_i18n if present
            if "group_i18n" in expanded_data:
                if "group_i18n" not in self.catalogs[name]:
                    self.catalogs[name]["group_i18n"] = {}
                self.catalogs[name]["group_i18n"].update(expanded_data["group_i18n"])

    def get_catalog_mode(self) -> str:
        """Return current catalog mode."""
        return self.catalog_mode

    def get_total_items(self) -> int:
        """Return total number of items across all catalogs (excluding colors)."""
        total = 0
        for catalog_name, catalog in self.catalogs.items():
            if catalog_name == "colors":
                continue
            if "items" in catalog:
                total += len(catalog["items"])
        return total

    @classmethod
    def normalize_language(cls, language: Optional[str]) -> str:
        """Normalize incoming locale code to supported language."""
        code = (language or "en").strip().lower()
        if code.startswith("zh"):
            return "zh"
        return "en"

    def get_item_localized_name(self, item: dict, language: str = "en") -> str:
        """Return localized display text for an item, with safe fallback."""
        lang = self.normalize_language(language)
        names = item.get("name_i18n")
        if isinstance(names, dict):
            localized = names.get(lang) or names.get("en")
            if isinstance(localized, str) and localized.strip():
                return localized
        return item.get("name", item.get("id", ""))

    def get_palette_localized_name(self, palette: dict, language: str = "en") -> str:
        """Return localized palette name with fallback."""
        lang = self.normalize_language(language)
        names = palette.get("name_i18n")
        if isinstance(names, dict):
            localized = names.get(lang) or names.get("en")
            if isinstance(localized, str) and localized.strip():
                return localized
        return palette.get("name", palette.get("id", ""))

    def localize_color_token(self, color_token: Optional[str], language: str = "en") -> Optional[str]:
        """Convert a canonical color token to localized display/output text."""
        if not color_token:
            return None
        lang = self.normalize_language(language)
        names = self.color_i18n.get(color_token)
        if isinstance(names, dict):
            localized = names.get(lang) or names.get("en")
            if isinstance(localized, str) and localized.strip():
                return localized
        return color_token

    def get_slot_item_by_id(self, slot_name: str, item_id: Optional[str]) -> Optional[dict]:
        """Resolve slot item dict by slot name + item id."""
        if not item_id or slot_name not in self.SLOT_DEFINITIONS:
            return None
        catalog_name = self.SLOT_DEFINITIONS[slot_name]["catalog"]
        return self.items_by_id.get(catalog_name, {}).get(item_id)

    def resolve_slot_item(self, slot_name: str, value_id: Optional[str], value_name: Optional[str]) -> Optional[dict]:
        """Resolve a slot item from either canonical id or legacy display name."""
        if slot_name not in self.SLOT_DEFINITIONS:
            return None
        catalog_name = self.SLOT_DEFINITIONS[slot_name]["catalog"]
        items_map = self.items_by_id.get(catalog_name, {})

        if value_id and value_id in items_map:
            return items_map[value_id]

        if value_name:
            name_key = value_name.strip().lower()
            mapped_id = self.item_id_by_name.get(catalog_name, {}).get(name_key)
            if mapped_id and mapped_id in items_map:
                return items_map[mapped_id]
        return None

    def resolve_slot_value_name(
        self,
        slot_name: str,
        value_id: Optional[str],
        value_name: Optional[str] = None,
        language: str = "en",
    ) -> Optional[str]:
        """Resolve localized slot text for a selected value id/name."""
        item = self.resolve_slot_item(slot_name, value_id, value_name)
        if not item:
            return None
        return self.get_item_localized_name(item, language)

    def get_slot_options(self, slot_name: str) -> List[dict]:
        """Get all available options for a slot."""
        if slot_name not in self.SLOT_DEFINITIONS:
            return []

        slot_def = self.SLOT_DEFINITIONS[slot_name]
        catalog_name = slot_def["catalog"]
        index_key = slot_def["index_key"]

        if catalog_name not in self.catalogs:
            return []

        catalog = self.catalogs[catalog_name]

        # Handle expressions (uses index_by_emotion_family)
        if catalog_name == "expressions":
            return catalog.get("items", [])

        # Handle poses/backgrounds (may have multiple indices)
        if index_key is None:
            items = catalog.get("items", [])
            # Keep pose slot focused on body poses; hand actions live in gesture slot.
            if catalog_name == "poses" and slot_name == "pose":
                return [item for item in items if item.get("category") != "gesture"]
            return items

        # Handle clothing (uses index_by_body_part)
        if catalog_name == "clothing":
            index = catalog.get("index_by_body_part", {})
            item_ids = index.get(index_key, [])
            items_map = self.items_by_id.get(catalog_name, {})
            return [items_map[id] for id in item_ids if id in items_map]

        # Handle other catalogs (hair, eyes, body) - uses index_by_category
        index = catalog.get("index_by_category", {})
        item_ids = index.get(index_key, [])
        items_map = self.items_by_id.get(catalog_name, {})
        return [items_map[id] for id in item_ids if id in items_map]

    def get_lower_body_covers_legs_by_id(self) -> Dict[str, bool]:
        """Return a map of lower_body item id -> whether it covers legs."""
        mapping: Dict[str, bool] = {}
        for item in self.get_slot_options("lower_body"):
            item_id = item.get("id")
            if not item_id:
                continue
            mapping[item_id] = bool(item.get("covers_legs", False))
        return mapping

    def lower_body_id_covers_legs(self, item_id: Optional[str]) -> bool:
        """Check whether a lower_body item id covers legs."""
        if not item_id:
            return False
        item = self.get_slot_item_by_id("lower_body", item_id)
        return bool(item and item.get("covers_legs", False))

    def _get_option_group(self, option: dict) -> Optional[str]:
        """Get the group key for an option item."""
        group = (
            option.get("style_group")
            or option.get("ui_group")
            or option.get("group")
            or option.get("emotion_family")
            or option.get("category")
        )
        if isinstance(group, str) and group.strip():
            return group.strip()
        return None

    def sample_slot(self, slot_name: str, disabled_groups: List[str] = None,
                    disabled_values: List[str] = None) -> Optional[dict]:
        """Randomly sample an item for a slot, excluding disabled groups and values."""
        options = self.get_slot_options(slot_name)
        if not options:
            return None

        if disabled_groups:
            options = [opt for opt in options
                       if self._get_option_group(opt) not in disabled_groups]
            if not options:
                return None

        if disabled_values:
            disabled_set = frozenset(disabled_values)
            options = [opt for opt in options
                       if opt.get("id") not in disabled_set]
            if not options:
                return None

        return random.choice(options)

    def get_palette_list(self) -> List[dict]:
        """Get list of available palettes."""
        return list(self.palettes.values())

    def sample_color_from_palette(self, palette_id: str) -> Optional[str]:
        """Sample a random color from a palette."""
        if palette_id not in self.palettes:
            return None
        palette = self.palettes[palette_id]
        colors = palette.get("colors", [])
        if not colors:
            return None
        return random.choice(colors)

    def sample_random_color(self) -> Optional[str]:
        """Sample a completely random color."""
        if not self.individual_colors:
            basic = ["white", "black", "red", "blue", "pink", "purple", "green", "yellow"]
            return random.choice(basic)
        return random.choice(self.individual_colors)

    def create_default_config(self) -> GeneratorConfig:
        """Create a default configuration with all slots."""
        config = GeneratorConfig()
        for slot_name in self.SLOT_DEFINITIONS:
            config.slots[slot_name] = SlotConfig()
        return config

    def randomize_slot(self, config: GeneratorConfig, slot_name: str,
                       include_color: bool = False, palette_id: Optional[str] = None) -> None:
        """Randomize a single slot in the config."""
        if slot_name not in config.slots:
            config.slots[slot_name] = SlotConfig()

        slot = config.slots[slot_name]
        if slot.locked:
            return

        item = self.sample_slot(slot_name)
        if item:
            slot.value = item.get("name", "")
            slot.value_id = item.get("id", "")
        else:
            slot.value = None
            slot.value_id = None

        # Handle color
        if include_color and self.SLOT_DEFINITIONS[slot_name].get("has_color", False):
            if palette_id and palette_id in self.palettes:
                slot.color = self.sample_color_from_palette(palette_id)
                slot.color_enabled = True
            elif config.color_mode == "random":
                slot.color = self.sample_random_color()
                slot.color_enabled = True

    def randomize_all(self, config: GeneratorConfig,
                      include_color: bool = False, palette_id: Optional[str] = None) -> None:
        """Randomize all non-locked slots."""
        for slot_name in self.SLOT_DEFINITIONS:
            if slot_name in config.slots and config.slots[slot_name].locked:
                continue
            self.randomize_slot(config, slot_name, include_color, palette_id)

        # Handle full_body logic
        if config.full_body_mode:
            self._apply_full_body_logic(config)
        self._apply_lower_body_leg_logic(config)

    def _apply_full_body_logic(self, config: GeneratorConfig) -> None:
        """Apply full_body override logic - if full_body is set, clear upper/lower."""
        full_body_slot = config.slots.get("full_body")
        if full_body_slot and full_body_slot.enabled and full_body_slot.value:
            for slot_name in ["upper_body", "lower_body"]:
                if slot_name in config.slots and not config.slots[slot_name].locked:
                    config.slots[slot_name].value = None
                    config.slots[slot_name].value_id = None

    def _apply_lower_body_leg_logic(self, config: GeneratorConfig) -> None:
        """If lower_body is an item that covers legs, clear legs slot value."""
        lower = config.slots.get("lower_body")
        legs = config.slots.get("legs")
        if not lower or not legs:
            return
        if not lower.enabled or not lower.value_id:
            return
        if self.lower_body_id_covers_legs(lower.value_id):
            legs.value = None
            legs.value_id = None

    def _apply_constraints(self, config: GeneratorConfig) -> None:
        """Apply constraint rules to fix nonsensical combinations."""
        from .constraints import ConstraintEngine
        engine = ConstraintEngine()
        results = {
            name: {"value_id": slot.value_id, "value": slot.value}
            for name, slot in config.slots.items()
        }
        engine.apply(
            results,
            lambda name, disabled_groups=None, disabled_values=None:
                self.sample_slot(name, disabled_groups=disabled_groups, disabled_values=disabled_values),
        )
        for name, result in results.items():
            if name in config.slots and not config.slots[name].locked:
                config.slots[name].value_id = result["value_id"]
                config.slots[name].value = result["value"]

    def get_catalog_stats(self) -> Dict[str, int]:
        """Return item counts per catalog."""
        stats = {}
        for catalog_name, catalog in self.catalogs.items():
            if catalog_name == "colors":
                continue
            if "items" in catalog:
                stats[catalog_name] = len(catalog["items"])
        return stats

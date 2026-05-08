"""
Slot-related API routes: definitions, options, randomization.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List, Optional

from . import deps
from .prompt import SlotState, GenerateRequest, build_prompt_string

router = APIRouter()

# Section layout sent to frontend so it can build the UI dynamically
SECTION_LAYOUT = {
    "appearance": {
        "label": "Appearance",
        "label_key": "section_appearance",
        "icon": "\U0001f464",
        "slots": [
            "hair_style", "hair_length", "hair_color", "hair_texture",
            "eye_color", "eye_expression_quality", "eye_shape", "eye_pupil_state",
            "eye_state", "eye_accessories",
        ],
        "columns": [
            ["hair_style", "hair_length", "hair_color", "hair_texture"],
            ["eye_color", "eye_expression_quality", "eye_shape", "eye_pupil_state", "eye_state", "eye_accessories"],
        ],
        "column_label_keys": ["section_appearance_hair", "section_appearance_eyes"],
    },
    "body": {
        "label": "Body / Expression / Pose",
        "label_key": "section_body",
        "icon": "\U0001f9cd",
        "slots": ["body_type", "height", "skin", "age_appearance",
                  "special_features", "expression", "view_angle", "pose", "gesture"],
    },
    "clothing": {
        "label": "Clothing & Background",
        "label_key": "section_clothing",
        "icon": "\U0001f457",
        "slots": ["head", "neck", "upper_body", "waist", "lower_body",
                  "full_body", "outerwear", "hands", "legs", "feet",
                  "accessory", "background"],
        "columns": [
            ["head", "neck", "upper_body", "waist", "lower_body", "full_body"],
            ["outerwear", "hands", "legs", "feet", "accessory", "background"],
        ],
    },
}


@router.get("/slots")
async def get_slots():
    """Return slot definitions, per-slot options, and section layout."""
    slots = {}
    for name, defn in deps.gen.SLOT_DEFINITIONS.items():
        full_options = deps.gen.get_slot_options_localized(name)
        slots[name] = {
            "category": defn["category"],
            "has_color": defn.get("has_color", False),
            "options": full_options,
        }
    return {
        "slots": slots,
        "sections": SECTION_LAYOUT,
        "lower_body_covers_legs_by_id": deps.gen.get_lower_body_covers_legs_by_id(),
        "pose_uses_hands_by_id": deps.gen.get_pose_uses_hands_by_id(),
    }


class RandomizeRequest(BaseModel):
    slot_names: List[str]
    locked: Dict[str, bool] = {}
    palette_enabled: bool = True
    palette_id: Optional[str] = None
    full_body_mode: bool = False
    upper_body_mode: bool = False
    current_values: Dict[str, Optional[str]] = {}
    slots: Dict[str, SlotState] = {}
    include_prompt: bool = False
    output_language: str = "en"
    disabled_groups: Dict[str, List[str]] = {}  # slot_name -> [group_keys]


@router.post("/randomize")
async def randomize_slots(req: RandomizeRequest):
    """Randomize specific slots. Returns {slot_name: {value_id, value, color}}."""
    results = {}
    full_body_value_id = req.current_values.get("full_body")

    for name in req.slot_names:
        if name not in deps.gen.SLOT_DEFINITIONS:
            continue
        if req.locked.get(name, False):
            continue

        slot_disabled_groups = req.disabled_groups.get(name, [])
        item = deps.gen.sample_slot(name, disabled_groups=slot_disabled_groups)
        value_id = item.get("id") if item else None
        value = item.get("name") if item else None

        if name == "full_body":
            full_body_value_id = value_id

        # Full-body override
        if (req.full_body_mode and name in ("upper_body", "lower_body")
                and full_body_value_id):
            value_id = None
            value = None

        color = None
        if deps.gen.SLOT_DEFINITIONS[name].get("has_color", False):
            if req.palette_enabled and req.palette_id:
                color = deps.gen.sample_color_from_palette(req.palette_id)

        results[name] = {"value_id": value_id, "value": value, "color": color}

    # Apply constraint rules to the subset of slots that were randomized
    constraint_changes = deps.constraints.apply(
        results,
        lambda name, disabled_groups=None, disabled_values=None:
            deps.gen.sample_slot(name, disabled_groups=disabled_groups, disabled_values=disabled_values),
    )

    payload = {"results": results}
    if constraint_changes:
        payload["constraint_changes"] = constraint_changes
    if req.include_prompt:
        for name, res in results.items():
            slot = req.slots.get(name)
            if not slot:
                slot = SlotState()
                req.slots[name] = slot
            slot.value_id = res["value_id"]
            slot.value = res["value"]
            slot.color = res["color"]
        prompt = build_prompt_string(
            GenerateRequest(
                slots=req.slots,
                full_body_mode=req.full_body_mode,
                upper_body_mode=req.upper_body_mode,
                output_language=req.output_language,
            )
        )
        payload["prompt"] = prompt
    return payload


class RandomizeAllRequest(BaseModel):
    locked: Dict[str, bool] = {}
    palette_enabled: bool = True
    palette_id: Optional[str] = None
    full_body_mode: bool = False
    upper_body_mode: bool = False
    slots: Dict[str, SlotState] = {}
    include_prompt: bool = False
    output_language: str = "en"
    disabled_groups: Dict[str, List[str]] = {}  # slot_name -> [group_keys]


@router.post("/randomize-all")
async def randomize_all(req: RandomizeAllRequest):
    """Randomize every non-locked slot. Returns full state."""
    results = {}
    full_body_value_id = None

    for name in deps.gen.SLOT_DEFINITIONS:
        if req.locked.get(name, False):
            continue

        slot_disabled_groups = req.disabled_groups.get(name, [])
        item = deps.gen.sample_slot(name, disabled_groups=slot_disabled_groups)
        value_id = item.get("id") if item else None
        value = item.get("name") if item else None

        if name == "full_body":
            full_body_value_id = value_id

        color = None
        if deps.gen.SLOT_DEFINITIONS[name].get("has_color", False):
            if req.palette_enabled and req.palette_id:
                color = deps.gen.sample_color_from_palette(req.palette_id)

        results[name] = {"value_id": value_id, "value": value, "color": color}

    # Include locked slot values so constraints can evaluate them
    for name, slot in req.slots.items():
        if req.locked.get(name, False) and (slot.value_id or slot.value):
            if name not in results:
                results[name] = {"value_id": slot.value_id, "value": slot.value, "color": slot.color}

    # Apply full-body override
    if req.full_body_mode and full_body_value_id:
        for name in ("upper_body", "lower_body"):
            if name in results and not req.locked.get(name, False):
                results[name]["value_id"] = None
                results[name]["value"] = None

    # Apply constraint rules to fix nonsensical combinations
    constraint_changes = deps.constraints.apply(
        results,
        lambda name, disabled_groups=None, disabled_values=None:
            deps.gen.sample_slot(name, disabled_groups=disabled_groups, disabled_values=disabled_values),
    )

    # Auto-assign palette colors to hair/eye if palette is active and slot not locked
    if req.palette_enabled and req.palette_id:
        for slot_name, body_part in [("hair_color", "hair"), ("eye_color", "eyes")]:
            if slot_name in results and not req.locked.get(slot_name, False):
                color_token = deps.gen.sample_color_from_palette(req.palette_id)
                if color_token:
                    localized = deps.gen.localize_color_token(color_token, req.output_language) or color_token
                    results[slot_name]["value"] = f"{localized} {body_part}"
                    results[slot_name]["value_id"] = None

    payload = {"results": results}
    if constraint_changes:
        payload["constraint_changes"] = constraint_changes
    if req.include_prompt:
        for name, res in results.items():
            slot = req.slots.get(name)
            if not slot:
                slot = SlotState()
                req.slots[name] = slot
            slot.value_id = res["value_id"]
            slot.value = res["value"]
            slot.color = res["color"]
        prompt = build_prompt_string(
            GenerateRequest(
                slots=req.slots,
                full_body_mode=req.full_body_mode,
                upper_body_mode=req.upper_body_mode,
                output_language=req.output_language,
            )
        )
        payload["prompt"] = prompt
    return payload


# ──────────────────────────────────────────────────────────────────────────────
# Catalog Mode Endpoints
# ──────────────────────────────────────────────────────────────────────────────

class CatalogModeRequest(BaseModel):
    mode: str  # "lightweight" or "expanded"


@router.get("/catalog-mode")
async def get_catalog_mode():
    """Return current catalog mode and item counts."""
    return {
        "mode": deps.gen.get_catalog_mode(),
        "item_count": deps.gen.get_total_items(),
        "catalog_stats": deps.gen.get_catalog_stats(),
        "available_modes": list(deps.gen.CATALOG_MODES),
    }


@router.post("/catalog-mode")
async def set_catalog_mode(req: CatalogModeRequest):
    """Switch between catalog modes.

    - lightweight: Curated items only (~500 items)
    - expanded: Includes auto-generated items from tags (~19,000+ items)
    """
    if req.mode not in deps.gen.CATALOG_MODES:
        return {
            "status": "error",
            "message": f"Invalid mode. Available modes: {list(deps.gen.CATALOG_MODES)}",
        }

    # Reinitialize generator with new mode
    deps.reinitialize_generator(catalog_mode=req.mode)

    return {
        "status": "ok",
        "mode": deps.gen.get_catalog_mode(),
        "item_count": deps.gen.get_total_items(),
        "catalog_stats": deps.gen.get_catalog_stats(),
    }

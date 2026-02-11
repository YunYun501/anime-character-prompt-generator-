"""
Prompt generation and palette application routes.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List, Optional

from generator.prompt_generator import PromptGenerator

router = APIRouter()
gen = PromptGenerator()

# Canonical slot order for prompt building (matches prompt_generator.py)
SLOT_ORDER = [
    "hair_color", "hair_length", "hair_style", "hair_texture",
    "eye_color", "eye_style",
    "body_type", "height", "skin", "age_appearance", "special_features",
    "expression",
    "full_body", "head", "neck", "upper_body", "waist", "lower_body",
    "outerwear", "hands", "legs", "feet", "accessory",
    "pose", "gesture",
    "background",
]


class SlotState(BaseModel):
    enabled: bool = True
    value: Optional[str] = None
    color: Optional[str] = None
    weight: float = 1.0


class GenerateRequest(BaseModel):
    slots: Dict[str, SlotState]
    full_body_mode: bool = True
    upper_body_mode: bool = False


@router.post("/generate-prompt")
async def generate_prompt(req: GenerateRequest):
    """Build the prompt string from provided slot state."""
    parts = ["1girl"]

    full_body_val = None
    fb = req.slots.get("full_body")
    if fb and fb.enabled and fb.value:
        full_body_val = fb.value

    lower_body_covers_legs = False
    lower = req.slots.get("lower_body")
    if lower and lower.enabled and lower.value:
        lower_body_covers_legs = gen.lower_body_value_covers_legs(lower.value)
    if req.full_body_mode and full_body_val:
        lower_body_covers_legs = False

    for name in SLOT_ORDER:
        slot = req.slots.get(name)
        if not slot or not slot.enabled or not slot.value:
            continue

        # Skip upper/lower if full_body active
        if req.full_body_mode and name in ("upper_body", "lower_body") and full_body_val:
            continue

        # Skip legs if lower-body item already covers legs.
        if name == "legs" and lower_body_covers_legs:
            continue

        part = f"{slot.color} {slot.value}" if slot.color else slot.value

        if slot.weight != 1.0:
            part = f"({part}:{slot.weight:.1f})"

        parts.append(part)

    return {"prompt": ", ".join(parts)}


class ApplyPaletteRequest(BaseModel):
    palette_id: str
    slots: Dict[str, SlotState]
    full_body_mode: bool = True
    upper_body_mode: bool = False


@router.post("/apply-palette")
async def apply_palette(req: ApplyPaletteRequest):
    """Apply palette colors to all has_color slots that have a value, then regenerate prompt."""
    new_colors = {}

    lower_body_covers_legs = False
    lower = req.slots.get("lower_body")
    if lower and lower.enabled and lower.value:
        lower_body_covers_legs = gen.lower_body_value_covers_legs(lower.value)
    full_body_active = False
    fb = req.slots.get("full_body")
    if fb and fb.enabled and fb.value and req.full_body_mode:
        full_body_active = True
    if full_body_active:
        lower_body_covers_legs = False

    for name, defn in gen.SLOT_DEFINITIONS.items():
        if not defn.get("has_color", False):
            continue
        if name == "legs" and lower_body_covers_legs:
            continue
        slot = req.slots.get(name)
        if slot and slot.value:
            color = gen.sample_color_from_palette(req.palette_id)
            new_colors[name] = color
            # Update the slot for prompt generation
            if name in req.slots:
                req.slots[name].color = color

    # Regenerate prompt with new colors
    gen_req = GenerateRequest(
        slots=req.slots,
        full_body_mode=req.full_body_mode,
        upper_body_mode=req.upper_body_mode,
    )
    prompt_result = await generate_prompt(gen_req)

    return {"colors": new_colors, "prompt": prompt_result["prompt"]}


@router.get("/palettes")
async def get_palettes():
    """Return all palettes and individual colors."""
    palettes = []
    for p in gen.palettes.values():
        palettes.append({
            "id": p["id"],
            "name": p.get("name", p["id"]),
            "colors": p.get("colors", []),
        })
    return {
        "palettes": palettes,
        "individual_colors": gen.individual_colors,
    }

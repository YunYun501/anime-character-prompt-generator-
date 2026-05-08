"""
Constraint engine for enforcing logical consistency between character slots.

Rules are declarative: they describe what triggers a constraint and what
action to take. The engine evaluates them against the current slot state
after randomization and applies fixes (clear, disable, or re-roll).

Rule types:
  - "blocks": If trigger slot has a trigger value, clear/disable target slots.
  - "conflicts": If trigger slot has a trigger value and target slot has a
    conflicting value, re-roll the target slot excluding those values.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
import random


@dataclass
class ConstraintRule:
    """A single constraint rule."""
    name: str
    type: str               # "blocks" | "conflicts"
    description: str
    trigger_slot: str       # Slot that activates this rule
    trigger_values: List[str]  # Value IDs that trigger the rule
    target_slots: List[str]  # Slots affected by this rule
    conflicting_values: List[str] = field(default_factory=list)  # For "conflicts" type


# ──────────────────────────────────────────────────────────────────────────────
# Rule Registry
#
# Rules are grouped by category. Each rule references item IDs that exist in
# the catalogs. If a catalog mode doesn't contain the trigger values, the
# rule simply doesn't fire — no error.
# ──────────────────────────────────────────────────────────────────────────────

CONSTRAINT_RULES: List[ConstraintRule] = [
    # ── Hair ──────────────────────────────────────────────────────────────
    ConstraintRule(
        name="helmet_hides_hair",
        type="blocks",
        description="Headwear that fully covers hair",
        trigger_slot="head",
        trigger_values=[
            "helmet",              # lightweight + expanded
            "kabuto_samurai_helmet",  # lightweight + expanded
            "motorcycle_helmet",   # expanded only
            "mail_coif",           # lightweight + expanded
            "mengu_armored_mask",  # lightweight + expanded
        ],
        target_slots=["hair_style", "hair_length", "hair_texture", "hair_color"],
    ),

    ConstraintRule(
        name="hood_hides_upward_hair",
        type="conflicts",
        description="Hood collides with upward hairstyles",
        trigger_slot="head",
        trigger_values=[
            "capes",  # hooded cape
        ],
        target_slots=["hair_style"],
        conflicting_values=[
            "high_ponytail", "updo", "half_updo", "chignon",
            "double_bun", "side_bun", "braided_bun", "messy_bun",
            "bun", "heart_ahoge", "double_ahoge", "ahoge",
            "antenna_hair",
        ],
    ),

    # ── Eyes ──────────────────────────────────────────────────────────────
    ConstraintRule(
        name="closed_eyes_no_expression_quality",
        type="blocks",
        description="Closed eyes can't have visible expression quality traits",
        trigger_slot="eye_state",
        trigger_values=["closed_eyes"],
        target_slots=["eye_expression_quality", "eye_pupil_state"],
    ),

    ConstraintRule(
        name="closed_eyes_conflicts_sparkle",
        type="conflicts",
        description="Closed eyes can't sparkle, pierce, or stare",
        trigger_slot="eye_state",
        trigger_values=["closed_eyes", "half_closed_eyes"],
        target_slots=["eye_expression_quality"],
        conflicting_values=[
            "sparkling_eyes", "bright_eyes", "glowing_eyes",
            "sharp_eyes", "expressive_eyes",
        ],
    ),

    ConstraintRule(
        name="eyepatch_blocks_eye_slots",
        type="blocks",
        description="Eyepatch covers one eye — clear pupil/state details",
        trigger_slot="eye_accessories",
        trigger_values=["eyepatch"],
        target_slots=["eye_pupil_state"],
    ),

    # Expanded-mode: blindfold blocks all eye detail slots
    ConstraintRule(
        name="blindfold_blocks_eye_details",
        type="blocks",
        description="Blindfold makes eye details invisible",
        trigger_slot="eye_accessories",
        trigger_values=["blindfold"],
        target_slots=["eye_state", "eye_expression_quality", "eye_shape",
                       "eye_pupil_state", "eye_color"],
    ),

    # Expanded-mode: sunglasses obscure eye details
    ConstraintRule(
        name="sunglasses_blocks_eye_quality",
        type="blocks",
        description="Sunglasses hide pupil/expression details",
        trigger_slot="eye_accessories",
        trigger_values=["sunglasses"],
        target_slots=["eye_pupil_state", "eye_expression_quality"],
    ),

    # ── Body ──────────────────────────────────────────────────────────────
    ConstraintRule(
        name="muscular_not_petite",
        type="conflicts",
        description="Muscular and petite/delicate are contradictory body types",
        trigger_slot="body_type",
        trigger_values=["muscular"],
        target_slots=["body_type"],  # self-referential (re-roll the same slot)
        conflicting_values=[
            "petite", "delicate", "lithe",
        ],
    ),

    ConstraintRule(
        name="plump_not_skinny",
        type="conflicts",
        description="Plump and skinny/lanky are contradictory",
        trigger_slot="body_type",
        trigger_values=["plump"],
        target_slots=["body_type"],
        conflicting_values=["skinny", "lanky"],
    ),

    # Expanded-mode: child/loli/toddler age → no adult body types
    ConstraintRule(
        name="young_age_not_adult_body",
        type="conflicts",
        description="Child/young age doesn't match adult body descriptors",
        trigger_slot="age_appearance",
        trigger_values=["child", "loli", "toddler", "young"],
        target_slots=["body_type"],
        conflicting_values=[
            "voluptuous", "muscular", "hourglass_figure",
        ],
    ),

    # ── Clothing ──────────────────────────────────────────────────────────────
    ConstraintRule(
        name="turtleneck_hides_neck_accessories",
        type="blocks",
        description="Turtleneck covers neck accessories",
        trigger_slot="neck",
        trigger_values=["turtleneck", "cowl_neck", "high_collar"],
        target_slots=["accessory"],  # could be more targeted if we had accessory sub-slots
    ),

    ConstraintRule(
        name="bare_feet_no_hosiery",
        type="conflicts",
        description="Bare feet conflict with socks/stockings on legs",
        trigger_slot="feet",
        trigger_values=["barefoot"],
        target_slots=["legs"],
        conflicting_values=[
            "stockings", "socks", "thigh_highs", "knee_highs",
            "ankle_socks", "pantyhose", "tights", "fishnet_stockings",
            "leg_warmers",
        ],
    ),

    ConstraintRule(
        name="gloves_hide_hand_jewelry",
        type="conflicts",
        description="Full gloves hide rings and bracelets",
        trigger_slot="hands",
        trigger_values=["gloves", "gauntlets", "armored_gauntlets", "mittens"],
        target_slots=["accessory"],
        conflicting_values=[
            "ring", "rings", "bracelet", "bracelets",
            "wristband", "watch", "bangle",
        ],
    ),

    # ── Expression ────────────────────────────────────────────────────────
    ConstraintRule(
        name="sleepy_expression_no_sparkle",
        type="blocks",
        description="Sleepy expression implies half-closed eyes — no sparkle",
        trigger_slot="expression",
        trigger_values=[
            "tired_sleepy_bored__sleepy_half-lidded",
            "tired_sleepy_bored__exhausted_dead_eyes",
            "tired_sleepy_bored__yawning",
        ],
        target_slots=["eye_expression_quality", "eye_pupil_state"],
    ),

    ConstraintRule(
        name="crying_expression_pupil_hidden",
        type="blocks",
        description="Heavy crying obscures pupil detail",
        trigger_slot="expression",
        trigger_values=[
            "sadness_hurt__crying_tears_streaming",
            "sadness_hurt__sobbing_ugly_cry_wailing",
            "extreme_anime_stylized__crying_waterfall_comedic",
        ],
        target_slots=["eye_pupil_state"],
    ),

    # ── Pose ──────────────────────────────────────────────────────────────
    ConstraintRule(
        name="lying_down_hair_gravity",
        type="conflicts",
        description="Upward hairstyles look wrong when lying down",
        trigger_slot="pose",
        trigger_values=[
            "lying_down", "lying_on_side", "lying_on_back",
            "lying_on_stomach", "reclining", "sleeping",
        ],
        target_slots=["hair_style"],
        conflicting_values=[
            "high_ponytail", "updo", "half_updo", "chignon",
            "drill_hair", "twin_drills",
        ],
    ),

    ConstraintRule(
        name="underwater_hair_texture",
        type="conflicts",
        description="Fluffy/voluminous hair behaves differently underwater",
        trigger_slot="pose",
        trigger_values=["underwater", "swimming", "diving"],
        target_slots=["hair_texture"],
        conflicting_values=[
            "fluffy", "voluminous", "floating_hair", "windswept_hair",
        ],
    ),

    # ── Background ────────────────────────────────────────────────────────
    ConstraintRule(
        name="bedroom_suggests_casual",
        type="conflicts",
        description="Bedroom setting conflicts with formal outerwear",
        trigger_slot="background",
        trigger_values=["bedroom", "bathroom"],
        target_slots=["outerwear"],
        conflicting_values=[
            "armor", "military_coat", "ceremonial_robe",
            "lab_coat", "hazmat_suit",
        ],
    ),

    ConstraintRule(
        name="beach_no_heavy_outerwear",
        type="conflicts",
        description="Beach setting doesn't match heavy coats",
        trigger_slot="background",
        trigger_values=["beach", "tropical_beach", "pool", "onsen", "hot_spring"],
        target_slots=["outerwear"],
        conflicting_values=[
            "winter_coat", "parka", "heavy_coat", "trench_coat",
            "fur_coat", "puffer_jacket",
        ],
    ),
]


class ConstraintEngine:
    """Evaluates constraint rules against current slot state."""

    def __init__(self, rules: Optional[List[ConstraintRule]] = None):
        self.rules = rules if rules is not None else CONSTRAINT_RULES

    def get_applicable_rules(self, slot_state: Dict[str, Optional[str]]) -> List[ConstraintRule]:
        """
        Find rules whose trigger condition is met by the current slot state.

        Args:
            slot_state: Dict of {slot_name: value_id} for currently-set slots.

        Returns:
            List of ConstraintRule objects that should be applied.
        """
        applicable = []
        for rule in self.rules:
            trigger_val = slot_state.get(rule.trigger_slot)
            if trigger_val and trigger_val in rule.trigger_values:
                applicable.append(rule)
        return applicable

    def get_disabled_values_for_slot(
        self, slot_name: str, slot_state: Dict[str, Optional[str]]
    ) -> Set[str]:
        """
        Return all value IDs that should be excluded when sampling a slot,
        based on currently-set values in other slots.

        Args:
            slot_name: The slot being sampled.
            slot_state: Current values of already-set slots.

        Returns:
            Set of value IDs to exclude.
        """
        excluded: Set[str] = set()
        for rule in self.get_applicable_rules(slot_state):
            if slot_name in rule.target_slots:
                if rule.type == "blocks":
                    # Blocks: ALL values are excluded (slot will be cleared)
                    # We don't add to excluded set — blocking is handled separately
                    pass
                elif rule.type == "conflicts":
                    excluded.update(rule.conflicting_values)
        return excluded

    def get_slots_to_disable(self, slot_state: Dict[str, Optional[str]]) -> Set[str]:
        """
        Return all slot names that should be cleared/disabled based on constraints.

        Args:
            slot_state: Current values of all slots.

        Returns:
            Set of slot names to clear.
        """
        disabled: Set[str] = set()
        for rule in self.get_applicable_rules(slot_state):
            if rule.type == "blocks":
                disabled.update(rule.target_slots)
        return disabled

    def apply(
        self,
        results: Dict[str, dict],
        sample_fn,
    ) -> List[dict]:
        """
        Apply all constraints to slot results. Modifies results in place.

        For "blocks" rules: clears the target slot values.
        For "conflicts" rules: re-rolls the target slot excluding conflicting values.

        Args:
            results: Dict of {slot_name: {value_id, value, color, ...}} from randomization.
            sample_fn: Callable(slot_name, disabled_values=list) → item dict for re-rolling.

        Returns:
            List of change records: [{slot, action, reason, ...}]
        """
        changes = []

        # Build a value_id-only lookup for constraint evaluation
        value_state: Dict[str, Optional[str]] = {}
        for name, res in results.items():
            value_state[name] = res.get("value_id")

        applicable = self.get_applicable_rules(value_state)

        for rule in applicable:
            if rule.type == "blocks":
                for target in rule.target_slots:
                    if target in results and results[target].get("value_id"):
                        results[target]["value_id"] = None
                        results[target]["value"] = None
                        changes.append({
                            "slot": target,
                            "action": "cleared",
                            "reason": rule.description,
                            "triggered_by": f"{rule.trigger_slot}={value_state.get(rule.trigger_slot)}",
                        })

            elif rule.type == "conflicts":
                for target in rule.target_slots:
                    if target not in results:
                        continue
                    current_val = results[target].get("value_id")
                    if current_val and current_val in rule.conflicting_values:
                        new_item = sample_fn(target, disabled_values=rule.conflicting_values)
                        results[target]["value_id"] = new_item.get("id") if new_item else None
                        results[target]["value"] = new_item.get("name") if new_item else None
                        changes.append({
                            "slot": target,
                            "action": "rerolled",
                            "reason": rule.description,
                            "triggered_by": f"{rule.trigger_slot}={value_state.get(rule.trigger_slot)}",
                            "excluded": rule.conflicting_values,
                        })

        return changes

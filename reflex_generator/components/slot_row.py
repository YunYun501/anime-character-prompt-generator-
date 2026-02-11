"""Slot row component for the Reflex prompt generator."""

import reflex as rx
from ..state import AppState
from ..styles import (
    slot_row_enabled, slot_row_disabled, button_on, button_off,
    button_small, select_style, weight_input
)
from ..utils import format_slot_name


def slot_row(slot_name: str, has_color: bool = False) -> rx.Component:
    """Create a slot row component.
    
    Args:
        slot_name: Name of the slot (e.g., "hair_style")
        has_color: Whether this slot has color selection
        
    Returns:
        A Reflex component representing the slot row
    """
    display_name = format_slot_name(slot_name)
    
    # Color components (only shown if has_color is True)
    color_components = []
    if has_color:
        color_components = [
            rx.select.root(
                rx.select.trigger(placeholder="Color..."),
                rx.select.content(
                    rx.foreach(
                        AppState.color_options,
                        lambda opt: rx.select.item(opt, value=opt),
                    ),
                ),
                value=AppState.slots[slot_name]["color"],
                on_change=lambda val: AppState.set_slot_color(slot_name, val),
                size="1",
            ),
            rx.button(
                "🎨",
                on_click=lambda: AppState.randomize_slot_color(slot_name),
                size="1",
            ),
        ]
    
    return rx.hstack(
        # On/Off button
        rx.button(
            rx.cond(
                AppState.slots[slot_name]["enabled"],
                "On",
                "Off",
            ),
            on_click=lambda: AppState.toggle_slot_enabled(slot_name),
            color_scheme=rx.cond(
                AppState.slots[slot_name]["enabled"],
                "green",
                "red",
            ),
            size="1",
            min_width="50px",
        ),
        
        # Constant (lock) button
        rx.button(
            rx.cond(
                AppState.slots[slot_name]["constant"],
                "🔒",
                "🔓",
            ),
            on_click=lambda: AppState.toggle_slot_constant(slot_name),
            size="1",
            variant="soft",
        ),
        
        # Slot label
        rx.text(
            display_name,
            weight=rx.cond(AppState.slots[slot_name]["enabled"], "bold", "regular"),
            color=rx.cond(AppState.slots[slot_name]["enabled"], "green", "gray"),
            min_width="120px",
        ),
        
        # Value dropdown
        rx.select.root(
            rx.select.trigger(placeholder="Select..."),
            rx.select.content(
                rx.foreach(
                    AppState.slot_options[slot_name],
                    lambda opt: rx.select.item(opt, value=opt),
                ),
            ),
            value=AppState.slots[slot_name]["value"],
            on_change=lambda val: AppState.set_slot_value(slot_name, val),
            size="2",
        ),
        
        # Randomize button
        rx.button(
            "🎲",
            on_click=lambda: AppState.randomize_slot(slot_name),
            size="1",
            variant="soft",
        ),
        
        # Color components (if any)
        *color_components,
        
        # Weight input
        rx.input(
            value=AppState.slots[slot_name]["weight"].to(str),
            on_change=lambda val: AppState.set_slot_weight(slot_name, val),
            type="number",
            min="0.1",
            max="2.0",
            step="0.1",
            width="60px",
            size="1",
        ),
        
        spacing="2",
        align="center",
        padding="6px 10px",
        border_radius="6px",
        border=rx.cond(
            AppState.slots[slot_name]["enabled"],
            "2px solid #22c55e",
            "2px solid #ef4444",
        ),
        background=rx.cond(
            AppState.slots[slot_name]["enabled"],
            "rgba(34, 197, 94, 0.08)",
            "rgba(239, 68, 68, 0.08)",
        ),
        opacity=rx.cond(AppState.slots[slot_name]["enabled"], "1", "0.5"),
        margin_y="2px",
        width="100%",
    )

"""Section container component for the Reflex prompt generator."""

import reflex as rx
from typing import List, Optional
from ..state import AppState
from ..styles import section_container, section_header
from .slot_row import slot_row


def section_container_component(
    title: str,
    section_id: str,
    slot_names: List[str],
    has_colors: Optional[List[bool]] = None
) -> rx.Component:
    """Create a section container with slots.
    
    Args:
        title: Section title (e.g., "Appearance")
        section_id: Section identifier for handlers (e.g., "appearance")
        slot_names: List of slot names in this section
        has_colors: List of booleans indicating if each slot has color (optional)
        
    Returns:
        A Reflex component representing the section
    """
    if has_colors is None:
        has_colors = [False] * len(slot_names)
    
    # Create slot rows
    slot_rows = []
    for i, slot_name in enumerate(slot_names):
        has_color = has_colors[i] if i < len(has_colors) else False
        slot_rows.append(slot_row(slot_name, has_color))
    
    return rx.box(
        # Section header
        rx.hstack(
            rx.text(title, weight="bold", size="4"),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    "🎲 Random",
                    on_click=lambda: AppState.randomize_section(section_id),
                    size="1",
                    variant="soft",
                ),
                rx.button(
                    "❌ All Off",
                    on_click=lambda: AppState.disable_section(section_id),
                    size="1",
                    variant="soft",
                ),
                rx.button(
                    "✅ All On",
                    on_click=lambda: AppState.enable_section(section_id),
                    size="1",
                    variant="soft",
                ),
                spacing="2",
            ),
            width="100%",
            align="center",
            padding_bottom="8px",
            border_bottom="2px solid #ddd",
            margin_bottom="8px",
        ),
        
        # Slot rows
        rx.vstack(
            *slot_rows,
            spacing="1",
            width="100%",
        ),
        
        padding="10px",
        border="1px solid #e5e7eb",
        border_radius="8px",
        margin="5px 0",
    )


def two_column_section(
    title: str,
    section_id: str,
    left_slots: List[str],
    right_slots: List[str],
    left_colors: Optional[List[bool]] = None,
    right_colors: Optional[List[bool]] = None
) -> rx.Component:
    """Create a two-column section container.
    
    Args:
        title: Section title
        section_id: Section identifier
        left_slots: Slot names for left column
        right_slots: Slot names for right column
        left_colors: Color flags for left column
        right_colors: Color flags for right column
        
    Returns:
        A Reflex component representing the two-column section
    """
    if left_colors is None:
        left_colors = [True] * len(left_slots)  # Clothing defaults to has_color=True
    if right_colors is None:
        right_colors = [True] * len(right_slots)
    
    # Create slot rows for left column
    left_rows = []
    for i, slot_name in enumerate(left_slots):
        has_color = left_colors[i] if i < len(left_colors) else True
        left_rows.append(slot_row(slot_name, has_color))
    
    # Create slot rows for right column
    right_rows = []
    for i, slot_name in enumerate(right_slots):
        has_color = right_colors[i] if i < len(right_colors) else True
        right_rows.append(slot_row(slot_name, has_color))
    
    return rx.box(
        # Section header
        rx.hstack(
            rx.text(title, weight="bold", size="4"),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    "🎲 Random Section",
                    on_click=lambda: AppState.randomize_section(section_id),
                    size="1",
                    variant="soft",
                ),
                rx.button(
                    "❌ All Off",
                    on_click=lambda: AppState.disable_section(section_id),
                    size="1",
                    variant="soft",
                ),
                rx.button(
                    "✅ All On",
                    on_click=lambda: AppState.enable_section(section_id),
                    size="1",
                    variant="soft",
                ),
                spacing="2",
            ),
            width="100%",
            align="center",
            padding_bottom="8px",
            border_bottom="2px solid #ddd",
            margin_bottom="8px",
        ),
        
        # Two columns
        rx.hstack(
            # Left column
            rx.box(
                rx.vstack(
                    *left_rows,
                    spacing="1",
                    width="100%",
                ),
                flex="1",
            ),
            
            # Right column
            rx.box(
                rx.vstack(
                    *right_rows,
                    spacing="1",
                    width="100%",
                ),
                flex="1",
            ),
            
            spacing="4",
            width="100%",
        ),
        
        padding="10px",
        border="1px solid #e5e7eb",
        border_radius="8px",
        margin="5px 0",
    )

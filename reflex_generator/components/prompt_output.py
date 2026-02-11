"""Prompt output component for the Reflex prompt generator."""

import reflex as rx
from ..state import AppState
from ..styles import output_textarea, button_primary, button_secondary, button_danger, row_flex
from ..utils import shutdown_server


def prompt_output() -> rx.Component:
    """Create the prompt output section.
    
    Returns:
        A Reflex component for the generated prompt output and action buttons
    """
    return rx.box(
        # Header
        rx.heading("Generated Prompt", size="5", margin_bottom="10px"),
        
        # Output textarea
        rx.text_area(
            value=AppState.generated_prompt,
            on_change=AppState.set_generated_prompt,
            style=output_textarea,
            rows="3",
            placeholder="Generated prompt will appear here...",
        ),
        
        # Action buttons
        rx.hstack(
            rx.button(
                "✨ Generate Prompt",
                on_click=AppState.generate_prompt,
                color_scheme="blue",
                size="2",
            ),
            rx.button(
                "🎲 Randomize All",
                on_click=AppState.randomize_all,
                color_scheme="green",
                size="2",
            ),
            rx.button(
                "📋 Copy",
                on_click=rx.set_clipboard(AppState.generated_prompt),
                size="2",
            ),
            rx.button(
                "🔄 Reset",
                on_click=AppState.reset_all,
                size="2",
            ),
            rx.button(
                "⏹ Stop Server",
                on_click=shutdown_server,
                color_scheme="red",
                size="2",
            ),
            spacing="3",
            margin_top="10px",
            flex_wrap="wrap",
        ),
        
        width="100%",
        padding="15px",
        border="1px solid #e5e7eb",
        border_radius="8px",
        margin_bottom="15px",
    )

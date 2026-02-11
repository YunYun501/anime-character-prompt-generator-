"""Settings panel component for the Reflex prompt generator."""

import reflex as rx
from ..state import AppState


def settings_panel() -> rx.Component:
    """Create the settings panel.
    
    Returns:
        A Reflex component for the settings panel
    """
    return rx.hstack(
        # Full-body mode checkbox
        rx.hstack(
            rx.checkbox(
                checked=AppState.full_body_mode,
                on_change=AppState.set_full_body_mode,
            ),
            rx.text("Full-body mode"),
            spacing="2",
            align="center",
        ),
        
        rx.divider(orientation="vertical", size="2"),
        
        # Color mode radio
        rx.hstack(
            rx.text("Color Mode:"),
            rx.radio_group(
                ["None", "Palette", "Random"],
                value=AppState.color_mode,
                on_change=AppState.set_color_mode,
                direction="row",
            ),
            spacing="2",
            align="center",
        ),
        
        rx.divider(orientation="vertical", size="2"),
        
        # Palette dropdown
        rx.hstack(
            rx.text("Palette:"),
            rx.select.root(
                rx.select.trigger(placeholder="Select palette..."),
                rx.select.content(
                    rx.foreach(
                        AppState.palette_options,
                        lambda opt: rx.select.item(opt, value=opt),
                    ),
                ),
                value=AppState.selected_palette,
                on_change=AppState.set_palette,
            ),
            spacing="2",
            align="center",
        ),
        
        spacing="4",
        align="center",
        flex_wrap="wrap",
        padding="10px",
        background_color="#f9fafb",
        border_radius="6px",
        margin="10px 0",
    )


def save_load_section() -> rx.Component:
    """Create the save/load configuration section.
    
    Returns:
        A Reflex component for save/load functionality
    """
    return rx.box(
        # Collapsible header
        rx.hstack(
            rx.hstack(
                rx.text("💾 Save / Load Configuration", weight="bold"),
                rx.text(
                    rx.cond(AppState.save_load_open, "▼", "▶"),
                    margin_left="10px",
                ),
                cursor="pointer",
                on_click=AppState.toggle_save_load,
            ),
            padding="10px",
            background_color="#f3f4f6",
            border_radius="6px",
            width="100%",
        ),
        
        # Collapsible content
        rx.cond(
            AppState.save_load_open,
            rx.box(
                # Save row
                rx.hstack(
                    rx.input(
                        value=AppState.config_name,
                        on_change=AppState.set_config_name,
                        placeholder="Configuration name...",
                        flex="1",
                    ),
                    rx.button(
                        "💾 Save",
                        on_click=AppState.save_config,
                        size="2",
                    ),
                    spacing="2",
                    margin_bottom="10px",
                    width="100%",
                ),
                
                # Load row
                rx.hstack(
                    rx.select.root(
                        rx.select.trigger(placeholder="Select config to load..."),
                        rx.select.content(
                            rx.foreach(
                                AppState.saved_configs,
                                lambda cfg: rx.select.item(cfg, value=cfg),
                            ),
                        ),
                        on_change=AppState.load_config,
                        flex="1",
                    ),
                    rx.button(
                        "🔄",
                        on_click=AppState.refresh_configs,
                        size="2",
                    ),
                    spacing="2",
                    margin_bottom="10px",
                    width="100%",
                ),
                
                # Status message
                rx.cond(
                    AppState.save_status != "",
                    rx.text(
                        AppState.save_status,
                        size="2",
                    ),
                    rx.fragment(),
                ),
                
                padding="10px",
                border="1px solid #e5e7eb",
                border_radius="6px",
                margin_top="10px",
            ),
            rx.fragment(),
        ),
        
        margin_top="15px",
        width="100%",
    )

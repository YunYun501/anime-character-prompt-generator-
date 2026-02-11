"""CSS Styles for the Reflex prompt generator UI."""

# Color constants
COLORS = {
    "enabled_border": "#22c55e",
    "enabled_bg": "rgba(34, 197, 94, 0.08)",
    "enabled_text": "#16a34a",
    "disabled_border": "#ef4444",
    "disabled_bg": "rgba(239, 68, 68, 0.08)",
    "disabled_text": "#9ca3af",
    "primary": "#3b82f6",
    "secondary": "#6b7280",
    "danger": "#ef4444",
}

# Base container style
container_style = {
    "max_width": "100%",
    "padding": "10px 20px",
}

# Slot row styles
slot_row_base = {
    "display": "flex",
    "align_items": "center",
    "gap": "10px",
    "padding": "6px 10px",
    "margin": "2px 0",
    "border_radius": "6px",
    "border": "2px solid",
}

slot_row_enabled = {
    **slot_row_base,
    "border_color": COLORS["enabled_border"],
    "background_color": COLORS["enabled_bg"],
}

slot_row_disabled = {
    **slot_row_base,
    "border_color": COLORS["disabled_border"],
    "background_color": COLORS["disabled_bg"],
    "opacity": "0.5",
}

# Button styles
button_primary = {
    "background_color": COLORS["primary"],
    "color": "white",
    "border": "none",
    "padding": "8px 16px",
    "border_radius": "4px",
    "cursor": "pointer",
}

button_secondary = {
    "background_color": COLORS["secondary"],
    "color": "white",
    "border": "none",
    "padding": "8px 16px",
    "border_radius": "4px",
    "cursor": "pointer",
}

button_danger = {
    "background_color": COLORS["danger"],
    "color": "white",
    "border": "none",
    "padding": "8px 16px",
    "border_radius": "4px",
    "cursor": "pointer",
}

button_small = {
    "padding": "4px 8px",
    "min_width": "35px",
    "font_size": "14px",
}

button_on = {
    "background_color": COLORS["enabled_border"],
    "color": "white",
    "min_width": "45px",
}

button_off = {
    "background_color": COLORS["disabled_border"],
    "color": "white",
    "min_width": "45px",
}

# Section styles
section_header = {
    "font_weight": "bold",
    "font_size": "1.1em",
    "padding": "8px",
    "border_bottom": "2px solid #ddd",
    "margin_bottom": "8px",
}

section_container = {
    "padding": "10px",
    "border": "1px solid #e5e7eb",
    "border_radius": "8px",
    "margin": "5px 0",
}

# Output area styles
output_textarea = {
    "font_size": "14px",
    "font_family": "monospace",
    "width": "100%",
    "min_height": "80px",
    "padding": "10px",
    "border": "1px solid #d1d5db",
    "border_radius": "6px",
}

# Select/dropdown styles
select_style = {
    "padding": "6px 10px",
    "border": "1px solid #d1d5db",
    "border_radius": "4px",
    "min_width": "150px",
}

# Weight input style
weight_input = {
    "width": "60px",
    "padding": "4px 8px",
    "border": "1px solid #d1d5db",
    "border_radius": "4px",
}

# Row layouts
row_flex = {
    "display": "flex",
    "gap": "10px",
    "align_items": "center",
}

row_space_between = {
    "display": "flex",
    "justify_content": "space-between",
    "align_items": "center",
    "gap": "10px",
}

# Grid for two columns
two_column_grid = {
    "display": "grid",
    "grid_template_columns": "1fr 1fr",
    "gap": "20px",
}

# Settings row
settings_row = {
    "display": "flex",
    "gap": "20px",
    "align_items": "center",
    "padding": "10px",
    "background_color": "#f9fafb",
    "border_radius": "6px",
    "margin": "10px 0",
}

# Accordion/collapsible styles
accordion_header = {
    "padding": "10px",
    "background_color": "#f3f4f6",
    "border_radius": "6px",
    "cursor": "pointer",
    "font_weight": "600",
}

# Label styles
label_enabled = {
    "color": COLORS["enabled_text"],
    "font_weight": "600",
}

label_disabled = {
    "color": COLORS["disabled_text"],
}

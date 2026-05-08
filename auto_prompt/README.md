# Random Character Prompt - ComfyUI Node

Auto-generates anime character prompts for Stable Diffusion.

## Installation

1. Copy the entire `auto_prompt` folder to `ComfyUI/custom_nodes/`
2. Copy the `prompt data` folder into `auto_prompt/` (see structure below)
3. Restart ComfyUI
4. Find **"Random Character Prompt"** in the node menu under **prompt** category

### Required Folder Structure

```
ComfyUI/
└── custom_nodes/
    └── auto_prompt/
        ├── __init__.py
        ├── nodes.py
        ├── prompt_generator.py
        ├── README.md
        └── prompt data/          <-- Copy this from main project
            ├── backgrounds/
            ├── body/
            ├── clothing/
            ├── colors/
            ├── expressions/
            ├── eyes/
            ├── hair/
            ├── poses/
            └── view_angles/
```

## Node Inputs

| Input | Type | Description |
|-------|------|-------------|
| seed | INT | Random seed for reproducible results |
| language | ENUM | Output language: "en" or "zh" |
| palette | ENUM | Color palette for clothing (or "none") |
| full_body_mode | BOOL | When enabled, full_body outfit skips upper/lower |
| upper_body_mode | BOOL | Skip lower body, legs, feet slots |
| prefix | STRING | Text prepended to prompt (e.g., quality tags) |
| lock_hair_color | STRING | Lock hair color (e.g., "blonde hair") |
| lock_eye_color | STRING | Lock eye color (e.g., "blue eyes") |
| lock_expression | STRING | Lock expression (e.g., "smile") |
| lock_pose | STRING | Lock pose (e.g., "standing") |
| lock_background | STRING | Lock background (e.g., "outdoor") |

## Node Output

| Output | Type | Description |
|--------|------|-------------|
| prompt | STRING | Generated prompt, connect to CLIP Text Encode |

## Example Workflow

```
[Random Character Prompt] → prompt → [CLIP Text Encode] → conditioning → [KSampler]
```

## Tips

- Use the **seed** input with a fixed value for reproducible characters
- Connect a random seed generator for variety
- Use **prefix** for quality tags like `(masterpiece),(best quality),(absurdres)`
- Lock specific attributes to maintain character consistency across generations

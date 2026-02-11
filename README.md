# Random Character Prompt Generator for Stable Diffusion

A local prompt-building tool for generating structured anime character prompts with slot-based randomization, palette-aware coloring, and live prompt updates.

## What This Project Does

- Builds prompts from configurable slots (appearance, body, clothing, background).
- Supports per-slot enable/disable, lock, randomize, weight, and optional color.
- Applies palette-based colors across clothing slots.
- Shows a colorized prompt preview (toggleable).
- Supports full-body and upper-body helper modes.
- Lets you save/load character configs as JSON.

The current primary UI is the FastAPI + vanilla HTML/JS app in `web/`.

## Quick Start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the FastAPI UI (recommended):

```bash
python run_Fastapi.py
```

The launcher auto-selects a free port from `8000-8099` and opens your browser.

## Other Launchers

- Reflex (experimental):

```bash
python run_reflex.py
```

## Core Features

- Live prompt sync: slot changes update prompt output immediately.
- Randomize all / section / slot with lock support.
- Palette controls: choose palette, randomize with palette colors, optional palette lock behavior in UI.
- Prompt prefix controls: optional always-include prefix (empty by default) and a preset for common SD quality tags.
- Clothing logic rules: lower-body items can declare `covers_legs`; selecting a covering lower-body item can one-shot disable legs.
- Upper-body mode behavior: one-shot disable helper, not a hard lock.

## Project Structure

- `run_Fastapi.py`: recommended local entry point.
- `web/server.py`: FastAPI app + static frontend + API routers.
- `web/static/`: HTML/CSS/JS frontend.
- `web/routes/`: backend APIs (`slots`, `prompt`, `configs`).
- `generator/prompt_generator.py`: catalog loading + randomization helpers.
- `colors/color_palettes.json`: palettes + individual colors.
- `clothing/clothing_list.json`: clothing catalog + `covers_legs` metadata.
- `configs/`: saved character preset JSON files.

## API Overview

- `GET /api/slots`
- `GET /api/palettes`
- `POST /api/randomize`
- `POST /api/randomize-all`
- `POST /api/generate-prompt`
- `POST /api/apply-palette`
- `GET /api/configs`
- `GET /api/configs/{name}`
- `POST /api/configs/{name}`

## Customizing Content

Edit JSON catalogs to add new options:

- Hair: `hair/hair_catalog.json`
- Eyes: `eyes/eye_catalog.json`
- Body features: `body/body_features.json`
- Expressions: `expressions/female_expressions.json`
- Clothing: `clothing/clothing_list.json`
- Poses: `poses/poses.json`
- Backgrounds: `backgrounds/backgrounds.json`
- Palettes/colors: `colors/color_palettes.json`

## Developer Docs

- Logic map: `DEVMAP.md`
- UI behavior spec: `UI_logic.md`

## Requirements

- Python 3.10+
- Dependencies in `requirements.txt`: `fastapi`, `uvicorn`, `reflex`.

## License

See `LICENSE`.

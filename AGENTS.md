# PySol Agent Notes

## Project Overview

PySol is a Klondike Solitaire desktop app built with Python and PySide6.

- `main.py` starts the Qt application.
- `window.py` owns the main window, top status labels, game view, and bottom toolbar.
- `controller.py` owns deck setup, pile layout, legal moves, stock/waste behavior, undo, hints, and win handling.
- `card.py` owns card rendering, card-back drawing, and drag interaction.
- `models.py` defines the `Pile` data structure.
- `constants.py` contains layout constants and card asset path helpers.
- Card faces are SVG files under `SVG-cards-1.3/`.
- Toolbar icons live under `assets/icons/`.

Be careful with existing uncommitted changes. Preserve unrelated user work and do not revert local edits unless explicitly asked.

## Running and Checking

Use the launcher when testing the app manually:

```bash
./run.sh
```

For a quick syntax check:

```bash
python3 -m py_compile main.py window.py controller.py card.py models.py constants.py
```

If a headless Qt smoke test is needed in this environment, this project has previously worked with:

```bash
PYENV_VERSION=3.13.0 \
PYTHONPATH=pysol_venv/lib/python3.13/site-packages \
QT_QPA_PLATFORM=offscreen \
python3.13 -c 'import sys; from PySide6.QtWidgets import QApplication; from window import SolitaireWindow; app = QApplication(sys.argv); w = SolitaireWindow(); w.show(); app.processEvents(); print("qt smoke ok")'
```

## Toolbar and Controls

The normal player-facing toolbar should stay focused on four controls:

- New Game
- Undo
- Hint
- Draw or Recycle Stock

Avoid reintroducing confusing player-facing Daily, Debug Force Win, Settings, or Play buttons unless the product intent changes. Debug helpers can remain in code, but should not appear in the normal toolbar by default.

Current toolbar icons are transparent PNGs:

- `assets/icons/new-game.png`
- `assets/icons/undo.png`
- `assets/icons/hint.png`
- `assets/icons/draw-stock.png`

The generated source images are preserved in `assets/icons/source/`.

## Creating Matching Images

Use the `imagegen` skill for new raster UI assets. The current toolbar icon style is:

- Polished modern game UI icon.
- Simple high-contrast shapes readable at small sizes.
- Slightly dimensional, but not photorealistic.
- Centered subject with generous but not excessive padding.
- No text, no watermark, no border frame.
- White playing cards, deep blue card-back accents, and a small bright accent color suited to the action.

For transparent toolbar assets, use the built-in image generation path first with a flat chroma-key background, then remove the key locally. A good prompt template:

```text
Use case: logo-brand
Asset type: PySide6 solitaire toolbar icon source for transparent PNG
Primary request: Create a clean, readable 1024x1024 icon for <ACTION> in a solitaire app: <SHORT SUBJECT DESCRIPTION>.
Style/medium: polished modern game UI icon, simple high-contrast shapes, slightly dimensional but not photorealistic
Composition/framing: centered subject, generous padding, readable at 32px, no border frame
Color palette: white playing cards, deep blue card-back accents, <ACTION ACCENT COLOR>, restrained highlights
Scene/backdrop: perfectly flat solid #00ff00 chroma-key background for background removal
Constraints: background must be one uniform #00ff00 color with no shadows, gradients, texture, reflections, floor plane, or lighting variation. Keep subject fully separated from background with crisp edges. Do not use #00ff00 anywhere in the subject. No text, no watermark.
```

After generation, copy the selected source image into `assets/icons/source/<name>-source.png`, then remove the chroma key into `assets/icons/<name>.png` with the installed helper:

```bash
/Users/matt.taylor/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 \
  /Users/matt.taylor/.codex/skills/.system/imagegen/scripts/remove_chroma_key.py \
  --input assets/icons/source/<name>-source.png \
  --out assets/icons/<name>.png \
  --auto-key border \
  --soft-matte \
  --transparent-threshold 12 \
  --opaque-threshold 220 \
  --despill
```

If the icon looks tiny inside the toolbar, crop transparent padding and normalize to a square PNG before use. The existing icons were tightened to `512x512` after background removal. Keep the subject filling most of the square while leaving a small transparent margin.

## Implementation Notes

- Prefer existing PySide6 patterns over introducing new UI frameworks.
- Keep button sizes stable and icon sizes explicit in `window.py`.
- Undo should snapshot pile membership, card face-up state, move count, and win state before meaningful moves.
- Hint should highlight a legal move without mutating game state.
- Stock draw/recycle should be undoable.

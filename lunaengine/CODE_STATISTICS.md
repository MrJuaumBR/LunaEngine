# LunaEngine Code Statistics

## Overview

- **Total Files**: 62
- **Total Lines**: 32862
- **Code Lines**: 22637
- **Comment Lines**: 5530
- **Blank Lines**: 4695

## Theme Statistics

- **Total Themes (base names)**: 62
- **Themes with both dark and light variants**: 62
- **Total variants (dark + light)**: 124

## UI Elements

- **Total UI Elements**: 29

## Code Density

- **Code Density**: 68.9%
- Balanced code and comments

## Project Structure

```bash
[ROT] lunaengine/
├── [PYT] __init__.py
├── [DIR] assets/
│   ├── [DIR] icons/
│   └── [DIR] shaders/
│       ├── [SHD] shaders.frag
│       ├── [SHD] shaders.geom
│       └── [SHD] shaders.vert
├── [DIR] backend/
│   ├── [PYT] __init__.py
│   ├── [PYT] controller.py
│   ├── [PYT] exceptions.py
│   ├── [PYT] network.py
│   ├── [PYT] openal.py
│   ├── [PYT] opengl.py
│   └── [PYT] types.py
├── [MDN] CODE_STATISTICS.md
├── [DIR] core/
│   ├── [PYT] __init__.py
│   ├── [PYT] audio.py
│   ├── [PYT] engine.py
│   ├── [PYT] renderer.py
│   ├── [PYT] scene.py
│   └── [PYT] window.py
├── [DIR] graphics/
│   ├── [PYT] __init__.py
│   ├── [PYT] camera.py
│   ├── [PYT] paperdoll.py
│   ├── [PYT] particles.py
│   ├── [PYT] shadows.py
│   └── [PYT] spritesheet.py
├── [DIR] misc/
│   ├── [PYT] __init__.py
│   ├── [PYT] debug.py
│   └── [PYT] icons.py
├── [DIR] storage/
│   ├── [PYT] __init__.py
│   ├── [PYT] atlas.py
│   ├── [PYT] encrypter.py
│   └── [PYT] savedata.py
├── [DIR] tools/
│   ├── [PYT] __init__.py
│   ├── [PYT] clear_pycache.py
│   ├── [PYT] code_stats.py
│   ├── [PYT] database_editor.py
│   └── [PYT] theme_tool.py
├── [DIR] ui/
│   ├── [PYT] __init__.py
│   ├── [DIR] elements/
│   │   ├── [PYT] __init__.py
│   │   ├── [PYT] base.py
│   │   ├── [PYT] buttons.py
│   │   ├── [PYT] clock.py
│   │   ├── [PYT] containers.py
│   │   ├── [PYT] dialogs.py
│   │   ├── [PYT] labels.py
│   │   ├── [PYT] misc.py
│   │   ├── [PYT] progress.py
│   │   ├── [PYT] selectors.py
│   │   ├── [PYT] textinputs.py
│   │   └── [PYT] visualizers.py
│   ├── [PYT] layer_manager.py
│   ├── [PYT] layout.py
│   ├── [PYT] notifications.py
│   ├── [PYT] styles.py
│   ├── [PYT] themes.py
│   ├── [PYT] tooltips.py
│   └── [PYT] tween.py
└── [DIR] utils/
    ├── [PYT] __init__.py
    ├── [PYT] image_converter.py
    ├── [PYT] math_utils.py
    ├── [PYT] performance.py
    ├── [PYT] threading.py
    └── [PYT] timer.py
```

## Files by Extension

| Extension | Count | Percentage |
|-----------|-------|------------|
| `.frag` | 1 | 1.6% |
| `.geom` | 1 | 1.6% |
| `.md` | 1 | 1.6% |
| `.py` | 58 | 93.5% |
| `.vert` | 1 | 1.6% |

## Files by Directory

| Directory | File Count |
|-----------|------------|
| `assets\shaders` | 3 |
| `backend` | 7 |
| `core` | 6 |
| `graphics` | 6 |
| `misc` | 3 |
| `root` | 2 |
| `storage` | 4 |
| `tools` | 5 |
| `ui` | 8 |
| `ui\elements` | 12 |
| `utils` | 6 |

## File Details

| File | Total Lines | Code | Comments | Blank | Size (KB) |
|------|------------|------|----------|-------|-----------|
| `backend\opengl.py` | 2207 | 1765 | 211 | 231 | 96.9 |
| `ui\elements\containers.py` | 2197 | 1847 | 74 | 276 | 92.5 |
| `ui\elements\selectors.py` | 1855 | 1521 | 71 | 263 | 77.6 |
| `misc\debug.py` | 1521 | 1150 | 137 | 234 | 66.3 |
| `core\engine.py` | 1485 | 897 | 330 | 258 | 60.4 |
| `ui\elements\visualizers.py` | 1306 | 1040 | 100 | 166 | 59.1 |
| `ui\tween.py` | 1202 | 550 | 423 | 229 | 36.7 |
| `graphics\camera.py` | 1105 | 643 | 266 | 196 | 43.4 |
| `backend\network.py` | 1092 | 770 | 140 | 182 | 40.1 |
| `ui\elements\textinputs.py` | 1064 | 879 | 71 | 114 | 45.3 |
| `ui\elements\labels.py` | 933 | 710 | 105 | 118 | 36.0 |
| `ui\notifications.py` | 931 | 576 | 199 | 156 | 37.9 |
| `graphics\spritesheet.py` | 930 | 469 | 309 | 152 | 33.3 |
| `storage\savedata.py` | 880 | 583 | 204 | 93 | 35.1 |
| `core\renderer.py` | 819 | 412 | 303 | 104 | 24.5 |
| `graphics\particles.py` | 742 | 580 | 78 | 84 | 23.9 |
| `ui\themes.py` | 716 | 554 | 65 | 97 | 26.3 |
| `ui\elements\base.py` | 682 | 359 | 211 | 112 | 26.7 |
| `backend\controller.py` | 652 | 503 | 63 | 86 | 23.5 |
| `core\audio.py` | 611 | 471 | 69 | 71 | 23.0 |
| `backend\openal.py` | 589 | 481 | 55 | 53 | 22.1 |
| `tools\database_editor.py` | 569 | 211 | 304 | 54 | 21.2 |
| `backend\types.py` | 485 | 353 | 51 | 81 | 17.2 |
| `assets\shaders\shaders.frag` | 440 | 368 | 15 | 57 | 14.4 |
| `utils\timer.py` | 427 | 164 | 179 | 84 | 13.8 |
| `tools\code_stats.py` | 423 | 296 | 56 | 71 | 17.3 |
| `utils\performance.py` | 422 | 304 | 44 | 74 | 14.9 |
| `graphics\paperdoll.py` | 411 | 213 | 130 | 68 | 15.7 |
| `graphics\shadows.py` | 411 | 278 | 74 | 59 | 16.2 |
| `ui\elements\clock.py` | 403 | 274 | 71 | 58 | 17.4 |
| `misc\icons.py` | 384 | 240 | 76 | 68 | 13.4 |
| `utils\math_utils.py` | 384 | 214 | 118 | 52 | 12.1 |
| `ui\elements\buttons.py` | 380 | 309 | 17 | 54 | 14.2 |
| `ui\tooltips.py` | 364 | 179 | 118 | 67 | 12.9 |
| `core\window.py` | 358 | 138 | 158 | 62 | 12.0 |
| `ui\elements\dialogs.py` | 303 | 210 | 47 | 46 | 12.4 |
| `ui\elements\progress.py` | 294 | 219 | 42 | 33 | 12.8 |
| `ui\elements\misc.py` | 280 | 207 | 29 | 44 | 10.7 |
| `utils\threading.py` | 263 | 155 | 77 | 31 | 10.0 |
| `storage\atlas.py` | 252 | 199 | 24 | 29 | 10.6 |
| `utils\image_converter.py` | 251 | 177 | 25 | 49 | 9.2 |
| `ui\layout.py` | 231 | 97 | 91 | 43 | 7.3 |
| `core\scene.py` | 214 | 150 | 20 | 44 | 7.9 |
| `CODE_STATISTICS.md` | 197 | 172 | 9 | 16 | 7.0 |
| `ui\layer_manager.py` | 165 | 110 | 31 | 24 | 6.3 |
| `tools\theme_tool.py` | 152 | 108 | 15 | 29 | 6.3 |
| `assets\shaders\shaders.vert` | 144 | 103 | 15 | 26 | 4.1 |
| `backend\__init__.py` | 135 | 100 | 28 | 7 | 2.9 |
| `graphics\__init__.py` | 100 | 72 | 21 | 7 | 2.0 |
| `ui\styles.py` | 91 | 35 | 38 | 18 | 2.7 |
| `utils\__init__.py` | 76 | 47 | 22 | 7 | 2.7 |
| `ui\__init__.py` | 73 | 26 | 30 | 17 | 2.7 |
| `core\__init__.py` | 52 | 26 | 20 | 6 | 1.2 |
| `ui\elements\__init__.py` | 48 | 24 | 22 | 2 | 2.1 |
| `storage\encrypter.py` | 45 | 35 | 0 | 10 | 1.3 |
| `assets\shaders\shaders.geom` | 27 | 20 | 3 | 4 | 0.7 |
| `tools\clear_pycache.py` | 24 | 20 | 0 | 4 | 0.8 |
| `backend\exceptions.py` | 21 | 5 | 11 | 5 | 0.6 |
| `misc\__init__.py` | 15 | 5 | 7 | 3 | 0.5 |
| `storage\__init__.py` | 15 | 9 | 4 | 2 | 0.5 |
| `__init__.py` | 11 | 4 | 3 | 4 | 0.3 |
| `tools\__init__.py` | 3 | 1 | 1 | 1 | 0.0 |

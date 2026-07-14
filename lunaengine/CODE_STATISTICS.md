# LunaEngine Code Statistics

## Overview

- **Total Files**: 72
- **Total Lines**: 31248
- **Code Lines**: 21240
- **Comment Lines**: 5357
- **Blank Lines**: 4651

## Theme Statistics

- **Total Themes (base names)**: 62
- **Themes with both dark and light variants**: 62
- **Total variants (dark + light)**: 124

## UI Elements

- **Total UI Elements**: 29

## Code Density

- **Code Density**: 68.0%
- Balanced code and comments

## Project Structure

```bash
[ROT] lunaengine/
├── [PYT] __init__.py
├── [DIR] assets/
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
│   ├── [DIR] shaders/
│   │   ├── [SHD] depth.frag
│   │   ├── [SHD] depth.geom
│   │   ├── [SHD] depth.vert
│   │   ├── [SHD] filter.frag
│   │   ├── [SHD] filter.vert
│   │   ├── [SHD] particle.comp
│   │   ├── [SHD] particle.frag
│   │   ├── [SHD] particle.vert
│   │   ├── [SHD] rounded_rect.frag
│   │   ├── [SHD] rounded_rect.vert
│   │   ├── [SHD] simple.frag
│   │   ├── [SHD] simple.vert
│   │   ├── [SHD] texture.frag
│   │   └── [SHD] texture.vert
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
│   └── [PYT] image_conversion_tool.py
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
| `.comp` | 1 | 1.4% |
| `.frag` | 6 | 8.3% |
| `.geom` | 1 | 1.4% |
| `.md` | 1 | 1.4% |
| `.py` | 57 | 79.2% |
| `.vert` | 6 | 8.3% |

## Files by Directory

| Directory | File Count |
|-----------|------------|
| `backend` | 7 |
| `core` | 6 |
| `graphics` | 6 |
| `graphics\shaders` | 14 |
| `misc` | 3 |
| `root` | 2 |
| `storage` | 4 |
| `tools` | 4 |
| `ui` | 8 |
| `ui\elements` | 12 |
| `utils` | 6 |

## File Details

| File | Total Lines | Code | Comments | Blank | Size (KB) |
|------|------------|------|----------|-------|-----------|
| `backend\opengl.py` | 2088 | 1258 | 478 | 352 | 84.7 |
| `ui\elements\containers.py` | 1998 | 1689 | 64 | 245 | 85.1 |
| `ui\elements\selectors.py` | 1769 | 1458 | 60 | 251 | 73.5 |
| `core\engine.py` | 1472 | 887 | 329 | 256 | 59.9 |
| `misc\debug.py` | 1428 | 1115 | 97 | 216 | 64.8 |
| `ui\elements\visualizers.py` | 1249 | 974 | 122 | 153 | 55.7 |
| `ui\tween.py` | 1202 | 550 | 423 | 229 | 36.7 |
| `graphics\camera.py` | 1105 | 643 | 266 | 196 | 43.4 |
| `backend\network.py` | 1092 | 770 | 140 | 182 | 40.1 |
| `ui\elements\textinputs.py` | 1034 | 865 | 67 | 102 | 44.5 |
| `ui\notifications.py` | 932 | 576 | 199 | 157 | 37.9 |
| `graphics\spritesheet.py` | 930 | 469 | 309 | 152 | 33.3 |
| `storage\savedata.py` | 880 | 583 | 204 | 93 | 35.1 |
| `ui\elements\labels.py` | 879 | 668 | 96 | 115 | 33.4 |
| `core\renderer.py` | 817 | 410 | 303 | 104 | 24.4 |
| `graphics\particles.py` | 742 | 580 | 78 | 84 | 23.9 |
| `ui\elements\base.py` | 682 | 359 | 212 | 111 | 26.8 |
| `ui\themes.py` | 664 | 509 | 63 | 92 | 24.2 |
| `backend\controller.py` | 652 | 503 | 63 | 86 | 23.5 |
| `core\audio.py` | 611 | 471 | 69 | 71 | 23.0 |
| `backend\openal.py` | 589 | 481 | 55 | 53 | 22.1 |
| `misc\icons.py` | 578 | 418 | 63 | 97 | 21.1 |
| `utils\timer.py` | 427 | 164 | 179 | 84 | 13.8 |
| `tools\code_stats.py` | 423 | 296 | 56 | 71 | 17.3 |
| `graphics\paperdoll.py` | 411 | 213 | 130 | 68 | 15.7 |
| `utils\performance.py` | 408 | 265 | 68 | 75 | 14.7 |
| `backend\types.py` | 407 | 296 | 37 | 74 | 14.3 |
| `ui\elements\clock.py` | 379 | 257 | 68 | 54 | 16.3 |
| `ui\tooltips.py` | 364 | 179 | 118 | 67 | 12.9 |
| `core\window.py` | 358 | 138 | 158 | 62 | 12.0 |
| `utils\math_utils.py` | 332 | 178 | 104 | 50 | 10.1 |
| `ui\elements\buttons.py` | 330 | 271 | 11 | 48 | 12.3 |
| `graphics\shaders\filter.frag` | 323 | 283 | 1 | 39 | 11.0 |
| `tools\image_conversion_tool.py` | 308 | 195 | 51 | 62 | 12.4 |
| `ui\elements\dialogs.py` | 293 | 202 | 47 | 44 | 11.8 |
| `ui\elements\misc.py` | 269 | 201 | 25 | 43 | 10.2 |
| `graphics\shadows.py` | 264 | 160 | 59 | 45 | 9.5 |
| `ui\elements\progress.py` | 263 | 196 | 39 | 28 | 11.5 |
| `storage\atlas.py` | 251 | 198 | 24 | 29 | 10.5 |
| `utils\image_converter.py` | 251 | 177 | 25 | 49 | 9.2 |
| `ui\layout.py` | 231 | 97 | 91 | 43 | 7.3 |
| `CODE_STATISTICS.md` | 217 | 192 | 9 | 16 | 8.0 |
| `core\scene.py` | 209 | 146 | 20 | 43 | 7.7 |
| `ui\layer_manager.py` | 165 | 110 | 31 | 24 | 6.3 |
| `backend\__init__.py` | 133 | 98 | 28 | 7 | 2.8 |
| `ui\styles.py` | 91 | 35 | 38 | 18 | 2.7 |
| `utils\threading.py` | 87 | 43 | 29 | 15 | 2.5 |
| `graphics\__init__.py` | 79 | 56 | 18 | 5 | 1.7 |
| `ui\__init__.py` | 73 | 26 | 30 | 17 | 2.7 |
| `utils\__init__.py` | 73 | 44 | 22 | 7 | 2.6 |
| `core\__init__.py` | 52 | 26 | 20 | 6 | 1.2 |
| `ui\elements\__init__.py` | 48 | 24 | 22 | 2 | 2.1 |
| `storage\encrypter.py` | 45 | 35 | 0 | 10 | 1.3 |
| `graphics\shaders\rounded_rect.frag` | 42 | 35 | 1 | 6 | 1.4 |
| `graphics\shaders\particle.vert` | 27 | 21 | 1 | 5 | 0.8 |
| `tools\clear_pycache.py` | 24 | 20 | 0 | 4 | 0.8 |
| `backend\exceptions.py` | 21 | 5 | 11 | 5 | 0.6 |
| `graphics\shaders\depth.geom` | 21 | 17 | 1 | 3 | 0.5 |
| `graphics\shaders\simple.vert` | 18 | 13 | 1 | 4 | 0.5 |
| `misc\__init__.py` | 18 | 8 | 7 | 3 | 0.9 |
| `graphics\shaders\rounded_rect.vert` | 17 | 14 | 1 | 2 | 0.4 |
| `graphics\shaders\texture.vert` | 17 | 14 | 1 | 2 | 0.5 |
| `storage\__init__.py` | 15 | 9 | 4 | 2 | 0.5 |
| `__init__.py` | 11 | 4 | 3 | 4 | 0.3 |
| `graphics\shaders\filter.vert` | 10 | 7 | 1 | 2 | 0.2 |
| `graphics\shaders\particle.comp` | 10 | 8 | 1 | 1 | 0.2 |
| `graphics\shaders\particle.frag` | 10 | 8 | 1 | 1 | 0.2 |
| `graphics\shaders\depth.vert` | 9 | 6 | 1 | 2 | 0.2 |
| `graphics\shaders\texture.frag` | 8 | 6 | 1 | 1 | 0.1 |
| `graphics\shaders\simple.frag` | 7 | 5 | 1 | 1 | 0.1 |
| `graphics\shaders\depth.frag` | 3 | 2 | 1 | 0 | 0.1 |
| `tools\__init__.py` | 3 | 1 | 1 | 1 | 0.0 |

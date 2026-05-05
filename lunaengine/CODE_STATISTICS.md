# LunaEngine Code Statistics

## Overview

- **Total Files**: 68
- **Total Lines**: 25048
- **Code Lines**: 16430
- **Comment Lines**: 4396
- **Blank Lines**: 4222

## Statistics

- **Total Themes**: 83
- **Total Elements**: 26

## Code Density

- **Code Density**: 65.6%
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
├── [DIR] tools/
│   ├── [PYT] __init__.py
│   ├── [PYT] clear_pycache.py
│   ├── [PYT] code_stats.py
│   ├── [PYT] image_conversion_tool.py
│   └── [PYT] split_themes.py
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
| `.comp` | 1 | 1.5% |
| `.frag` | 6 | 8.8% |
| `.geom` | 1 | 1.5% |
| `.md` | 1 | 1.5% |
| `.py` | 53 | 77.9% |
| `.vert` | 6 | 8.8% |

## Files by Directory

| Directory | File Count |
|-----------|------------|
| `backend` | 7 |
| `core` | 6 |
| `graphics` | 5 |
| `graphics\shaders` | 14 |
| `misc` | 3 |
| `root` | 2 |
| `tools` | 5 |
| `ui` | 8 |
| `ui\elements` | 12 |
| `utils` | 6 |

## File Details

| File | Total Lines | Code | Comments | Blank | Size (KB) |
|------|------------|------|----------|-------|-----------|
| `backend\opengl.py` | 1612 | 1135 | 201 | 276 | 66.7 |
| `ui\elements\selectors.py` | 1592 | 1304 | 36 | 252 | 68.1 |
| `ui\tween.py` | 1202 | 550 | 423 | 229 | 36.7 |
| `ui\elements\containers.py` | 1192 | 1020 | 10 | 162 | 54.5 |
| `core\engine.py` | 1148 | 556 | 363 | 229 | 43.4 |
| `backend\network.py` | 1092 | 770 | 140 | 182 | 40.1 |
| `ui\notifications.py` | 932 | 576 | 199 | 157 | 37.9 |
| `graphics\spritesheet.py` | 930 | 446 | 331 | 153 | 33.4 |
| `graphics\camera.py` | 881 | 514 | 197 | 170 | 34.2 |
| `ui\elements\textinputs.py` | 871 | 700 | 12 | 159 | 35.9 |
| `ui\elements\visualizers.py` | 838 | 670 | 28 | 140 | 36.6 |
| `misc\debug.py` | 826 | 630 | 62 | 134 | 36.2 |
| `core\audio.py` | 774 | 431 | 200 | 143 | 26.1 |
| `backend\openal.py` | 766 | 433 | 185 | 148 | 25.5 |
| `graphics\particles.py` | 742 | 580 | 78 | 84 | 23.9 |
| `backend\controller.py` | 640 | 493 | 63 | 84 | 23.0 |
| `ui\themes.py` | 638 | 496 | 53 | 89 | 23.0 |
| `misc\icons.py` | 578 | 418 | 63 | 97 | 21.1 |
| `ui\elements\base.py` | 439 | 235 | 127 | 77 | 16.9 |
| `utils\timer.py` | 427 | 164 | 179 | 84 | 13.8 |
| `utils\performance.py` | 408 | 265 | 68 | 75 | 14.7 |
| `backend\types.py` | 401 | 291 | 37 | 73 | 14.0 |
| `tools\code_stats.py` | 400 | 274 | 56 | 70 | 16.1 |
| `ui\elements\clock.py` | 394 | 224 | 102 | 68 | 16.3 |
| `ui\tooltips.py` | 364 | 179 | 118 | 67 | 12.9 |
| `core\window.py` | 358 | 138 | 158 | 62 | 12.0 |
| `core\renderer.py` | 339 | 96 | 187 | 56 | 11.3 |
| `utils\math_utils.py` | 332 | 178 | 104 | 50 | 10.1 |
| `graphics\shaders\filter.frag` | 323 | 283 | 1 | 39 | 11.0 |
| `tools\image_conversion_tool.py` | 308 | 195 | 51 | 62 | 12.4 |
| `graphics\shadows.py` | 264 | 160 | 59 | 45 | 9.5 |
| `ui\elements\buttons.py` | 251 | 207 | 4 | 40 | 9.9 |
| `utils\image_converter.py` | 251 | 177 | 25 | 49 | 9.2 |
| `ui\layout.py` | 231 | 97 | 91 | 43 | 7.3 |
| `ui\layer_manager.py` | 225 | 94 | 85 | 46 | 7.5 |
| `ui\elements\dialogs.py` | 224 | 159 | 24 | 41 | 9.1 |
| `ui\elements\misc.py` | 221 | 161 | 14 | 46 | 8.3 |
| `CODE_STATISTICS.md` | 203 | 181 | 8 | 14 | 7.5 |
| `core\scene.py` | 191 | 142 | 10 | 39 | 7.0 |
| `ui\elements\progress.py` | 170 | 142 | 3 | 25 | 7.3 |
| `ui\elements\labels.py` | 150 | 119 | 2 | 29 | 6.0 |
| `backend\__init__.py` | 108 | 80 | 22 | 6 | 2.2 |
| `ui\styles.py` | 91 | 35 | 38 | 18 | 2.7 |
| `utils\threading.py` | 87 | 43 | 29 | 15 | 2.5 |
| `graphics\__init__.py` | 77 | 53 | 19 | 5 | 1.7 |
| `ui\__init__.py` | 73 | 26 | 30 | 17 | 2.7 |
| `utils\__init__.py` | 73 | 44 | 22 | 7 | 2.6 |
| `tools\split_themes.py` | 61 | 43 | 7 | 11 | 2.1 |
| `ui\elements\__init__.py` | 48 | 24 | 22 | 2 | 2.1 |
| `graphics\shaders\rounded_rect.frag` | 42 | 35 | 1 | 6 | 1.4 |
| `core\__init__.py` | 28 | 7 | 15 | 6 | 0.8 |
| `graphics\shaders\particle.vert` | 27 | 21 | 1 | 5 | 0.8 |
| `tools\clear_pycache.py` | 24 | 20 | 0 | 4 | 0.8 |
| `backend\exceptions.py` | 21 | 5 | 11 | 5 | 0.6 |
| `graphics\shaders\depth.geom` | 21 | 17 | 1 | 3 | 0.5 |
| `graphics\shaders\simple.vert` | 18 | 13 | 1 | 4 | 0.5 |
| `graphics\shaders\rounded_rect.vert` | 17 | 14 | 1 | 2 | 0.4 |
| `graphics\shaders\texture.vert` | 17 | 14 | 1 | 2 | 0.5 |
| `misc\__init__.py` | 16 | 6 | 7 | 3 | 0.9 |
| `__init__.py` | 11 | 4 | 3 | 4 | 0.3 |
| `graphics\shaders\filter.vert` | 10 | 7 | 1 | 2 | 0.2 |
| `graphics\shaders\particle.comp` | 10 | 8 | 1 | 1 | 0.2 |
| `graphics\shaders\particle.frag` | 10 | 8 | 1 | 1 | 0.2 |
| `graphics\shaders\depth.vert` | 9 | 6 | 1 | 2 | 0.2 |
| `graphics\shaders\texture.frag` | 8 | 6 | 1 | 1 | 0.1 |
| `graphics\shaders\simple.frag` | 7 | 5 | 1 | 1 | 0.1 |
| `graphics\shaders\depth.frag` | 3 | 2 | 1 | 0 | 0.1 |
| `tools\__init__.py` | 3 | 1 | 1 | 1 | 0.0 |

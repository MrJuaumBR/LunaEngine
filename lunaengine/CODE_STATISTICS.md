# LunaEngine Code Statistics

## Overview

- **Total Files**: 56
- **Total Lines**: 29098
- **Code Lines**: 19150
- **Comment Lines**: 5657
- **Blank Lines**: 4291

## Statistics

- **Total Themes**: 83
- **Total Elements**: 26

## Code Density

- **Code Density**: 65.8%
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
│   ├── [PYT] bones.py
│   └── [PYT] icons.py
├── [DIR] tools/
│   ├── [PYT] __init__.py
│   ├── [PYT] code_stats.py
│   └── [PYT] image_conversion_tool.py
├── [DIR] ui/
│   ├── [PYT] __init__.py
│   ├── [PYT] elements.py
│   ├── [PYT] layer_manager.py
│   ├── [PYT] layout.py
│   ├── [PYT] notifications.py
│   ├── [PYT] styles.py
│   ├── [JSN] themes.json
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
| `.comp` | 1 | 1.8% |
| `.frag` | 6 | 10.7% |
| `.geom` | 1 | 1.8% |
| `.json` | 1 | 1.8% |
| `.md` | 1 | 1.8% |
| `.py` | 40 | 71.4% |
| `.vert` | 6 | 10.7% |

## Files by Directory

| Directory | File Count |
|-----------|------------|
| `backend` | 7 |
| `core` | 6 |
| `graphics` | 5 |
| `graphics\shaders` | 14 |
| `misc` | 3 |
| `root` | 2 |
| `tools` | 3 |
| `ui` | 10 |
| `utils` | 6 |

## File Details

| File | Total Lines | Code | Comments | Blank | Size (KB) |
|------|------------|------|----------|-------|-----------|
| `ui\elements.py` | 6997 | 3935 | 1790 | 1272 | 273.3 |
| `ui\themes.json` | 4816 | 4816 | 0 | 0 | 188.1 |
| `backend\opengl.py` | 1363 | 961 | 154 | 248 | 53.7 |
| `ui\tween.py` | 1202 | 550 | 423 | 229 | 36.7 |
| `core\engine.py` | 1112 | 527 | 360 | 225 | 41.9 |
| `backend\network.py` | 1092 | 770 | 140 | 182 | 40.1 |
| `ui\notifications.py` | 932 | 576 | 199 | 157 | 37.9 |
| `graphics\camera.py` | 881 | 514 | 197 | 170 | 34.2 |
| `core\audio.py` | 774 | 431 | 200 | 143 | 26.1 |
| `backend\openal.py` | 766 | 433 | 185 | 148 | 25.5 |
| `graphics\particles.py` | 742 | 580 | 78 | 84 | 23.9 |
| `backend\controller.py` | 640 | 493 | 63 | 84 | 23.0 |
| `graphics\spritesheet.py` | 613 | 279 | 223 | 111 | 21.5 |
| `misc\icons.py` | 578 | 418 | 63 | 97 | 21.1 |
| `ui\themes.py` | 567 | 402 | 82 | 83 | 19.9 |
| `misc\bones.py` | 493 | 313 | 72 | 108 | 20.5 |
| `utils\timer.py` | 427 | 164 | 179 | 84 | 13.8 |
| `tools\code_stats.py` | 400 | 274 | 56 | 70 | 16.1 |
| `utils\performance.py` | 377 | 238 | 66 | 73 | 13.3 |
| `ui\tooltips.py` | 364 | 179 | 118 | 67 | 12.9 |
| `core\window.py` | 358 | 138 | 158 | 62 | 12.0 |
| `core\renderer.py` | 339 | 96 | 187 | 56 | 11.3 |
| `utils\math_utils.py` | 332 | 178 | 104 | 50 | 10.1 |
| `graphics\shaders\filter.frag` | 323 | 283 | 1 | 39 | 11.0 |
| `tools\image_conversion_tool.py` | 308 | 195 | 51 | 62 | 12.4 |
| `graphics\shadows.py` | 264 | 160 | 59 | 45 | 9.5 |
| `utils\image_converter.py` | 251 | 177 | 25 | 49 | 9.2 |
| `ui\layout.py` | 231 | 97 | 91 | 43 | 7.3 |
| `ui\layer_manager.py` | 225 | 94 | 85 | 46 | 7.5 |
| `backend\types.py` | 187 | 135 | 19 | 33 | 6.1 |
| `core\scene.py` | 181 | 133 | 10 | 38 | 6.8 |
| `CODE_STATISTICS.md` | 180 | 155 | 9 | 16 | 6.3 |
| `backend\__init__.py` | 104 | 76 | 22 | 6 | 2.2 |
| `ui\styles.py` | 91 | 35 | 38 | 18 | 2.7 |
| `utils\threading.py` | 87 | 43 | 29 | 15 | 2.5 |
| `graphics\__init__.py` | 77 | 53 | 19 | 5 | 1.7 |
| `ui\__init__.py` | 73 | 26 | 30 | 17 | 2.7 |
| `utils\__init__.py` | 73 | 44 | 22 | 7 | 2.6 |
| `graphics\shaders\rounded_rect.frag` | 42 | 35 | 1 | 6 | 1.4 |
| `core\__init__.py` | 28 | 7 | 15 | 6 | 0.8 |
| `graphics\shaders\particle.vert` | 27 | 21 | 1 | 5 | 0.8 |
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

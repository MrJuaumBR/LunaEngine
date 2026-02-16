# LunaEngine Code Statistics

## Overview

- **Total Files**: 42
- **Total Lines**: 29470
- **Code Lines**: 18998
- **Comment Lines**: 5998
- **Blank Lines**: 4474

## Theme Statistics

- **Total Themes**: 83

## Code Density

- **Code Density**: 64.5%
- Balanced code and comments

## Project Structure

```bash
📁 lunaengine/
├── 🐍 __init__.py
├── 📁 backend/
│   ├── 🐍 __init__.py
│   ├── 🐍 controller.py
│   ├── 🐍 exceptions.py
│   ├── 🐍 network.py
│   ├── 🐍 openal.py
│   ├── 🐍 opengl.py
│   └── 🐍 types.py
├── 📝 CODE_STATISTICS.md
├── 📁 core/
│   ├── 🐍 __init__.py
│   ├── 🐍 audio.py
│   ├── 🐍 engine.py
│   ├── 🐍 renderer.py
│   ├── 🐍 scene.py
│   └── 🐍 window.py
├── 📁 graphics/
│   ├── 🐍 __init__.py
│   ├── 🐍 camera.py
│   ├── 🐍 particles.py
│   ├── 🐍 shadows.py
│   └── 🐍 spritesheet.py
├── 📁 misc/
│   ├── 🐍 __init__.py
│   ├── 🐍 bones.py
│   └── 🐍 icons.py
├── 📁 tools/
│   ├── 🐍 __init__.py
│   ├── 🐍 code_stats.py
│   └── 🐍 image_conversion_tool.py
├── 📁 ui/
│   ├── 🐍 __init__.py
│   ├── 🐍 elements.py
│   ├── 🐍 layer_manager.py
│   ├── 🐍 layout.py
│   ├── 🐍 notifications.py
│   ├── 🐍 styles.py
│   ├── 📋 themes.json
│   ├── 🐍 themes.py
│   ├── 🐍 tooltips.py
│   └── 🐍 tween.py
└── 📁 utils/
    ├── 🐍 __init__.py
    ├── 🐍 image_converter.py
    ├── 🐍 math_utils.py
    ├── 🐍 performance.py
    ├── 🐍 threading.py
    └── 🐍 timer.py
```

## Files by Extension

| Extension | Count | Percentage |
|-----------|-------|------------|
| `.json` | 1 | 2.4% |
| `.md` | 1 | 2.4% |
| `.py` | 40 | 95.2% |

## Files by Directory

| Directory | File Count |
|-----------|------------|
| `backend` | 7 |
| `core` | 6 |
| `graphics` | 5 |
| `misc` | 3 |
| `root` | 2 |
| `tools` | 3 |
| `ui` | 10 |
| `utils` | 6 |

## File Details

| File | Total Lines | Code | Comments | Blank | Size (KB) |
|------|------------|------|----------|-------|-----------|
| `ui\elements.py` | 6966 | 3926 | 1769 | 1271 | 270.9 |
| `ui\themes.json` | 4816 | 4816 | 0 | 0 | 188.1 |
| `backend\opengl.py` | 2466 | 1596 | 402 | 468 | 93.2 |
| `ui\tween.py` | 1202 | 550 | 423 | 229 | 36.7 |
| `backend\network.py` | 1092 | 770 | 140 | 182 | 40.1 |
| `core\engine.py` | 989 | 439 | 346 | 204 | 36.4 |
| `ui\notifications.py` | 932 | 576 | 199 | 157 | 37.9 |
| `graphics\camera.py` | 814 | 483 | 174 | 157 | 31.8 |
| `core\audio.py` | 774 | 431 | 200 | 143 | 26.1 |
| `backend\openal.py` | 766 | 433 | 185 | 148 | 25.5 |
| `graphics\particles.py` | 693 | 465 | 128 | 100 | 24.4 |
| `backend\controller.py` | 640 | 493 | 63 | 84 | 23.0 |
| `graphics\spritesheet.py` | 613 | 279 | 223 | 111 | 21.5 |
| `misc\icons.py` | 578 | 418 | 63 | 97 | 21.1 |
| `ui\themes.py` | 567 | 402 | 82 | 83 | 19.9 |
| `misc\bones.py` | 493 | 313 | 72 | 108 | 20.5 |
| `utils\timer.py` | 427 | 164 | 179 | 84 | 13.8 |
| `graphics\shadows.py` | 392 | 247 | 65 | 80 | 15.4 |
| `utils\performance.py` | 377 | 238 | 66 | 73 | 13.3 |
| `tools\code_stats.py` | 369 | 249 | 55 | 65 | 14.8 |
| `ui\tooltips.py` | 364 | 179 | 118 | 67 | 12.9 |
| `core\window.py` | 358 | 138 | 158 | 62 | 12.0 |
| `core\scene.py` | 333 | 124 | 139 | 70 | 11.7 |
| `core\renderer.py` | 332 | 93 | 184 | 55 | 11.1 |
| `tools\image_conversion_tool.py` | 308 | 195 | 51 | 62 | 12.4 |
| `utils\math_utils.py` | 268 | 131 | 95 | 42 | 8.4 |
| `utils\image_converter.py` | 251 | 177 | 25 | 49 | 9.2 |
| `ui\layout.py` | 231 | 97 | 91 | 43 | 7.3 |
| `ui\layer_manager.py` | 225 | 94 | 85 | 46 | 7.5 |
| `backend\types.py` | 187 | 135 | 19 | 33 | 6.1 |
| `CODE_STATISTICS.md` | 139 | 117 | 8 | 14 | 4.5 |
| `ui\styles.py` | 91 | 35 | 38 | 18 | 2.7 |
| `utils\threading.py` | 87 | 43 | 29 | 15 | 2.5 |
| `graphics\__init__.py` | 73 | 49 | 19 | 5 | 1.7 |
| `ui\__init__.py` | 73 | 26 | 30 | 17 | 2.7 |
| `utils\__init__.py` | 69 | 40 | 22 | 7 | 2.4 |
| `backend\__init__.py` | 36 | 14 | 16 | 6 | 1.8 |
| `core\__init__.py` | 28 | 7 | 15 | 6 | 0.8 |
| `backend\exceptions.py` | 21 | 5 | 11 | 5 | 0.6 |
| `misc\__init__.py` | 16 | 6 | 7 | 3 | 0.9 |
| `__init__.py` | 11 | 4 | 3 | 4 | 0.3 |
| `tools\__init__.py` | 3 | 1 | 1 | 1 | 0.0 |

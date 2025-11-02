# LunaEngine 🚀

A modern, optimized 2D game engine built with Python and Pygame featuring advanced UI systems, procedural lighting, and embedded asset management.

## 📋 Features

| Feature | Description | Status |
|---------|-------------|---------|
| **Advanced UI** | Roblox Studio-like UI components | ✅ Functional |
| **OpenGL Rendering** | Hardware-accelerated graphics | ✅ Functional |
| **Performance Tools** | FPS monitoring, hardware detection | ✅ Functional |
| **Themes** | The engine have pre-built themes | ✅ Functional |
| **Lighting System** | Dynamic lights and shadows | 🔄 WIP |
| **Particle Effects** | Particle system | 🔄 WIP |
| **Image Embedding** | Convert assets to Python code | ⚠️ Buggy |
| **Modular Architecture** | Easy to extend and customize | |

# Code
[See this file](./lunaengine/CODE_STATISTICS.md)
[TestPyPi](https://test.pypi.org/project/lunaengine/)
[PyPi](https://pypi.org/project/lunaengine/)

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run a basic example
python examples/basic_game.py
```

## Requirements

### Core Dependencies (required):

```bash
pygame>=2.5.0
numpy>=1.21.0
PyOpenGL>=3.1.0
PyOpenGL-accelerate>=3.1.0
```

### Development Tools (optional):

```bash
black>=22.0.0
flake8>=4.0.0
pytest>=7.0.0
setuptools>=65.0.0
wheel>=0.37.0
twine>=4.0.0
```

## Build
```bash
# Make build
python -m build

# Check files
twine check dist/* 

# Upload testpypi
twine upload --config-file .pypirc --repository testpypi dist/*

# Upload PyPi
twine upload --config-file .pypirc --repository pypi dist/*
```

## OpenGL
- Require OpenGL 3.3+
- ``LunaEngine("Game Title", screen_width, screen_height, use_opengl=True)``
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

## 📁 Project Structure
```bash
LunaEngine/
├── examples/ # Demo applications
│   ├── basic_game.py # Basic UI demonstration
│   ├── image_conversion_demo.py # Image embedding system
│   ├── performance_demo.py # Comprehensive performance demo
│   ├── working.py # ???
│   ├── snake_demo.py # A Snake game made with the engine
│   ├── ui_comprehensive_demo.py # All Ui items used :)
│   └── comprehensive_demo.py # All features combined
├── lunaengine/ # Engine source code
│   ├── CODE_STATISTICS.md # Code metrics (generated)
│   ├── core/ # Core engine systems
│   │   ├── engine.py # Main engine class
│   │   ├── window.py # Window management
│   │   └── renderer.py # Abstract renderer
│   ├── ui/ # UI system
│   │   ├── elements.py # UI components (Buttons, Sliders, etc.)
│   │   ├── layout.py # Layout managers
│   │   ├── themes.py # All Themes from engine(You can create customs too.)
│   │   └── styles.py # UI theming system
│   ├── graphics/ # Graphics subsystems
│   │   ├── spritesheet.py # Sprite sheet management
│   │   ├── lighting.py # Dynamic lighting system
│   │   ├── shadows.py # Shadow rendering
│   │   └── particles.py # Particle effects
│   ├── utils/ # Utility modules
│   │   ├── image_converter.py # Image embedding tools
│   │   ├── performance.py # Performance monitoring
│   │   ├── math_utils.py # Math helpers
│   │   └── threading.py # Thread management
│   ├── backend/ # Renderer backends
│   │   ├── opengl.py # OpenGL renderer
│   │   └── pygame_backend.py # Pygame renderer
├── └── tools/ # Development tools
│       ├── generate_documentation.py # Uses Ollama to generate docs
│       ├── code_stats.py # Code statistics analyzer
│       └── image_conversion_tool.py # Image conversion CLI
└── requirements.txt # Dependencies
```


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


# Installation

This guide will help you set up LunaEngine on your system.

## System Requirements

- **Python** 3.9 or higher (not tested on older versions)
- **OpenGL** 3.3+ capable graphics card (required for rendering)
- **Operating System**: Windows or Linux (macOS and Google devices are not officially supported)

## Supported Operating Systems

The engine officially supports:
- ✅ **Windows** – Full support
- ✅ **Linux** – Full support
- ❌ **macOS** – Not officially supported
- ❌ **Google devices** – Not officially supported

> **Note**: The engine uses OpenGL 3.3+ and does not plan to add 3D support. It remains a simple 2D framework.

## Installation Methods

### Method 1: Install from PyPI (Recommended)

The easiest way to install LunaEngine is via pip:

```bash
pip install lunaengine
```

### Method 2: Install from TestPyPi

If you want to test the latest pre-release version:
```bash
pip install -i https://test.pypi.org/simple/ lunaengine
```

### Method 3: Install from Source

For development or to get the absolute latest version:

```bash
# Clone the repository
git clone https://github.com/MrJuaumBR/LunaEngine.git
cd LunaEngine

# Install dependencies
pip install -r requirements.txt

# Install the package in development mode
pip install -e .
```

### Verifying Installation

To verify that LunaEngine is correctly installed, create a simple test script:

```python
from lunaengine.core.engine import Engine

# Create engine instance
engine = Engine()

# Print version information
print("LunaEngine is ready!")
print(f"OpenGL Version: {engine.renderer.get_opengl_version()}")
```

run the script:

```bash
python test.py
```

If no errors appear, the installation was successful!

## Common Issues

### OpenGL Version Error

**Error message:** ``OpenGL version 3.3 or higher is required``

**Solution:** Update your graphics drivers. If you're on an older system, ensure your GPU supports OpenGL 3.3+.

### Missing Dependencies

**Error message:** ``ModuleNotFoundError: No module named 'pygame'``

**Solution:** Install the required dependencies manually:

```bash
pip install pygame>=2.5.0 numpy>=1.21.0 PyOpenGL>=3.1.0 PyOpenGL-accelerate>=3.1.0 PyOpenAL
```

### Windows DLL Issues

If you encounter DLL-related errors on Windows, try installing Microsoft Visual C++ Redistributables from the official Microsoft website.

### What's next?

Once installation is complete, proceed to the **Introduction** lesson to learn the basics of using LunaEngine

## Additional Resources
- [GitHub Repository](https://github.com/MrJuaumBR/LunaEngine)
- [Official Documentation](https://mrjuaumbr.github.io/LunaEngine/)
- [Discord Community](https://discord.gg/fb84sHDX7R)


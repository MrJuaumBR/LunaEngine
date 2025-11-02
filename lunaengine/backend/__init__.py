"""Backend module for LunaEngine

LOCATION: lunaengine/backend/__init__.py

DESCRIPTION:
Initialization file for the backend module. This module provides rendering 
backends and graphics system implementations for the LunaEngine.

MODULES PROVIDED:
- opengl: OpenGL-based renderer for hardware-accelerated graphics
- pygame_backend: Pygame-based fallback renderer for compatibility

LIBRARIES USED:
- pygame: Core graphics and window management
- OpenGL: 3D graphics rendering (optional)
- numpy: Numerical operations for graphics math
"""

from .opengl import OpenGLRenderer, TextureShader, ParticleShader, ShaderProgram
from .pygame_backend import PygameRenderer

__all__ = [
    "OpenGLRenderer", "TextureShader", "ParticleShader", "ShaderProgram", "PygameRenderer"
]
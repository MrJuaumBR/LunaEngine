"""
LunaEngine Core Module
=====================

This module contains the core components of the LunaEngine game engine.
It provides the main engine class, scene management, rendering system, and window management.

Classes:
    - LunaEngine: Main game engine class
    - Scene: Base class for all game scenes  
    - Renderer: Abstract base class for renderers
    - Window: Window management class

Imports:
    - pygame: For game window and input handling
    - typing: For type hints
    - abc: For abstract base classes
"""

from .engine import LunaEngine
from .scene import Scene
from .renderer import Renderer
from .window import Window
from .audio import AudioSystem, AudioEvent, AudioState, AudioChannel

engine = LunaEngine

__all__ = ["LunaEngine", "engine", "Scene", "Renderer", "Window", "AudioSystem", "AudioEvent", "AudioState", "AudioChannel"]
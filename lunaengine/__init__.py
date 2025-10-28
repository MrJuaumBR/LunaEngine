"""
LunaEngine - A modern 2D game engine
"""

__version__ = "0.1.0"
__author__ = "Your Name"

from .core.engine import LunaEngine
from .core.window import Window
from .ui.elements import *
from .ui.layout import *
from .ui.styles import *
from .graphics.spritesheet import SpriteSheet
from .graphics.lighting import LightSystem, Light
from .graphics.shadows import ShadowSystem
from .graphics.particles import ParticleSystem, ParticleEmitter

__all__ = [
    'LunaEngine',
    'Window',
    'SpriteSheet', 
    'LightSystem',
    'Light',
    'ShadowSystem',
    'ParticleSystem',
    'ParticleEmitter',
]
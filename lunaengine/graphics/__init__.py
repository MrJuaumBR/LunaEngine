"""
Graphics Module - Advanced Rendering and Visual Effects for LunaEngine

LOCATION: lunaengine/graphics/__init__.py

DESCRIPTION:
Initialization file for the graphics module. This module provides advanced
rendering capabilities, visual effects, and graphics utilities for creating
visually rich 2D games. Includes particle systems, lighting, shadows, and
sprite management.

MODULES PROVIDED:
- lighting: Dynamic lighting system with multiple light sources
- particles: Particle effects and emitter management
- shadows: Real-time shadow casting and occlusion
- spritesheet: Sprite sheet parsing and animation frame management

LIBRARIES USED:
- pygame: Core graphics operations and surface management
- numpy: Mathematical operations and performance optimization
- math: Trigonometric functions and geometric calculations
- typing: Type hints for better code documentation

This module enables developers to create immersive visual experiences with
dynamic lighting, particle effects, and professional sprite animation.
"""

from .spritesheet import SpriteSheet, Animation
from .particles import ParticleSystem, ParticleConfig, ParticleType, PhysicsType, ExitPoint
from .camera import Camera, CameraMode, CameraShakeType
from .shadows import ShadowSystem, ShadowCaster, PerformanceLevel, Light, ShadowTechnique

__all__ = [
    "SpriteSheet",
    "Animation",
    "ParticleSystem",
    "ParticleConfig",
    "ParticleType",
    "PhysicsType",
    "ExitPoint",
    "Camera",
    "CameraMode",
    "CameraShakeType",
    "ShadowSystem",
    "ShadowCaster",
    "PerformanceLevel",
    "Light",
    "ShadowTechnique",
]
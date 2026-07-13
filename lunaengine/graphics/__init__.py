"""
Graphics Module - Advanced Rendering and Visual Effects for LunaEngine

LOCATION: lunaengine/graphics/__init__.py

DESCRIPTION:
Initialization file for the graphics module. Exports all public classes,
enums, and utilities for rendering, camera, particles, shadows, and sprites.

"""

from .spritesheet import SpriteSheet, Animation
from .particles import (
    ParticleSystem,
    ThreadedParticleSystem,
    ParticleConfig,
    ParticleType,
    ExitPoint,
    PhysicsType,
)
from .camera import (
    # Main class
    Camera,
    # Enums
    CameraMode,
    CameraShakeType,
    InterpolationType,
    # Follow strategies (for customisation)
    FollowStrategy,
    SimpleFollow,
    FixedFollow,
    PlatformerFollow,
    TopDownFollow,
    # Constraints
    CameraConstraints,
    # Effects
    CameraEffect,
    ShakeEffect,
    TraumaEffect,
    # Parallax
    ParallaxLayer,
    ParallaxBackground,
)
from .shadows import ShadowSystem, ShadowCaster, Light, LightType
from .paperdoll import Layer, Paperdoll
from .paperdoll import Animation as PaperDollAnimation

__all__ = [
    # Sprite
    "SpriteSheet",
    "Animation",
    # Particles
    "ParticleSystem",
    "ThreadedParticleSystem",
    "ParticleConfig",
    "ParticleType",
    "ExitPoint",
    "PhysicsType",
    # Camera
    "Camera",
    "CameraMode",
    "CameraShakeType",
    "InterpolationType",
    "FollowStrategy",
    "SimpleFollow",
    "FixedFollow",
    "PlatformerFollow",
    "TopDownFollow",
    "CameraConstraints",
    "CameraEffect",
    "ShakeEffect",
    "TraumaEffect",
    "ParallaxLayer",
    "ParallaxBackground",
    # Shadows
    "ShadowSystem", "ShadowCaster", 'Light', "LightType",
    # Paperdoll
    "Layer", "Paperdoll", "PaperDollAnimation"
]
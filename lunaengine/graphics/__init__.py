"""
Graphics Module - Advanced Rendering and Visual Effects for LunaEngine

LOCATION: lunaengine/graphics/__init__.py

DESCRIPTION:
Initialization file for the graphics module. Exports all public classes,
enums, and utilities for rendering, camera, particles, shadows, and sprites.

"""

from .image import Image
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

from .shadows import (
    SCSManager,
    ShadowCaster,
    LightCaster,
    ColorKeys,
    # utility functions
    pixel_to_centimeter,
    centimeter_to_pixel,
    meter_to_pixel,
)

# Paperdoll
from .paperdoll import Layer, Paperdoll
from .paperdoll import Animation as PaperDollAnimation

__all__ = [
    # Sprite
    "Image",
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
    # NEW Shadows (replaces old ShadowSystem, Light, LightType)
    "SCSManager",
    "ShadowCaster",
    "LightCaster",
    "ColorKeys",
    # Units
    "pixel_to_centimeter",
    "centimeter_to_pixel",
    "meter_to_pixel",
    # Paperdoll
    "Layer",
    "Paperdoll",
    "PaperDollAnimation"
]

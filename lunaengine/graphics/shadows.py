"""
lunaengine/graphics/shadows.py

Simple shadow system: data management + CPU‑based projected shadows.
"""

import math
import pygame
from enum import Enum
from typing import List, Tuple, Optional, Union
from pygame.math import Vector2

# ----------------------------------------------------------------------
# Enums (kept for extensibility)
# ----------------------------------------------------------------------

class LightType(Enum):
    POINT = "point"
    DIRECTIONAL = "directional"

class LightShape(Enum):
    CIRCLE = "circle"
    RECTANGLE = "rectangle"
    CONE = "cone"

class ShadowType(Enum):
    TRANSLUCENT = "translucent"
    OPAQUE = "opaque"
    BLUR = "blur"

class ShadowShape(Enum):
    CIRCLE = "circle"
    RECTANGLE = "rectangle"
    CONE = "cone"
    POLYGON = "polygon"

# ----------------------------------------------------------------------
# Light (data only)
# ----------------------------------------------------------------------

class Light:
    """Light source that can cast shadows."""
    def __init__(
        self,
        light_type: LightType,
        position: Tuple[float, float],
        color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        intensity: float = 1.0,
        range: float = 10.0,
        cast_shadows: bool = True
    ):
        self.light_type = light_type
        self.position = Vector2(position)
        self.color = color
        self.intensity = intensity
        self.range = range
        self.cast_shadows = cast_shadows
        self.visible = True

# ----------------------------------------------------------------------
# ShadowCaster (data only)
# ----------------------------------------------------------------------

class ShadowCaster:
    """An object that can cast shadows."""
    def __init__(
        self,
        vertices: List[Tuple[float, float]],
        position: Tuple[float, float] = (0, 0),
        visible: bool = True
    ):
        self.vertices = vertices          # list of (x, y) in local space (relative to position)
        self.position = Vector2(position)
        self.visible = visible

# ----------------------------------------------------------------------
# ShadowSystem (manager + simple rendering)
# ----------------------------------------------------------------------

class ShadowSystem:
    """Manages lights and casters, and renders simple projected shadows."""
    def __init__(self):
        self.lights: List[Light] = []
        self.casters: List[ShadowCaster] = []
        self.enabled = False
        
        self.darkness: float = 0.3
        self.stretch: float = 2.0
        self.cap_at_range: bool = True

    def add_light(self, light: Light):
        self.lights.append(light)

    def remove_light(self, light: Light):
        if light in self.lights:
            self.lights.remove(light)

    def clear_lights(self):
        self.lights.clear()

    def add_caster(self, caster: ShadowCaster):
        self.casters.append(caster)

    def remove_caster(self, caster: ShadowCaster):
        if caster in self.casters:
            self.casters.remove(caster)

    def clear_casters(self):
        self.casters.clear()

    # Helper methods for creating common casters
    def add_rectangle_caster(self, x: float, y: float, width: float, height: float) -> ShadowCaster:
        """Create a rectangular caster (centered at x,y)."""
        half_w = width / 2
        half_h = height / 2
        vertices = [
            (-half_w, -half_h),
            ( half_w, -half_h),
            ( half_w,  half_h),
            (-half_w,  half_h)
        ]
        caster = ShadowCaster(vertices, position=(x, y))
        self.add_caster(caster)
        return caster

    def add_circle_caster(self, x: float, y: float, radius: float, segments: int = 16) -> ShadowCaster:
        """Create a circular caster approximated by a polygon."""
        vertices = []
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            vertices.append((math.cos(angle) * radius, math.sin(angle) * radius))
        caster = ShadowCaster(vertices, position=(x, y))
        self.add_caster(caster)
        return caster

    def add_point_light(self, x: float, y: float, color=(1,1,1), intensity=1.0, range=100.0) -> Light:
        """Helper to create a point light."""
        light = Light(LightType.POINT, (x, y), color, intensity, range)
        self.add_light(light)
        return light

    def add_directional_light(self, color=(1,1,1), intensity=1.0, range=500.0, *args, **kwargs) -> Light:
        """Helper to create a directional light (simulated with a distant point)."""
        # Position is far away; direction will be computed from object to this point.
        light = Light(LightType.DIRECTIONAL, (-1000, -1000), color, intensity, range)
        self.add_light(light)
        return light

    def render_shadows_simple(self, renderer, camera):
        """
        Draw simple projected shadows for all lights and casters.
        
        Args:
            renderer: The OpenGLRenderer instance.
            camera: The camera (to convert world to screen).
        """
        if not self.enabled:
            return

        # For each light
        for light in self.lights:
            if not light.visible or not light.cast_shadows:
                continue

            light_pos = light.position  # world position

            # For each caster
            for caster in self.casters:
                if not caster.visible:
                    continue

                # Vector from light to caster center
                to_caster = caster.position - light_pos
                dist = to_caster.length()
                if dist < 0.1:
                    continue  # light inside object – skip

                direction = to_caster / dist

                # Shadow length: stretch factor times distance, optionally capped at light's range
                shadow_len = dist * self.stretch
                if self.cap_at_range:
                    shadow_len = min(shadow_len, light.range)

                # Build shadow polygon by offsetting each vertex
                shadow_world = []
                for v in caster.vertices:
                    world_v = caster.position + Vector2(v)
                    # Project away from light
                    proj = world_v + direction * shadow_len
                    shadow_world.append(proj)

                # Convert to screen coordinates
                shadow_screen = [camera.world_to_screen(p) for p in shadow_world]
                pts = [(int(p.x), int(p.y)) for p in shadow_screen]

                # Draw as a semi‑transparent polygon
                shadow_color = (0, 0, 0, int(255 * self.darkness))
                renderer.draw_polygon(pts, shadow_color, fill=True)

    def apply_lighting(self, renderer, camera, ambient: float = 0.2, light_power: float = 1.0, saturation: float = 0.5):
        """
        Darken areas outside any light's range and brighten areas inside lights.
        
        Args:
            renderer: The OpenGLRenderer instance.
            camera: The camera (to convert world to screen).
            ambient: Base brightness of unlit areas (0.0 = pitch black, 1.0 = fully bright).
            light_power: Overall brightness multiplier for lights (higher = brighter).
            saturation: How much the light's color affects the scene (0.0 = white light only,
                        1.0 = full color). Values between 0 and 1 mix the light color with white.
        """
        if not self.enabled:
            return
        # 1. Draw fullscreen darkness overlay (ambient lighting)
        # We use normal blending to darken the scene.
        darkness_alpha = int(255 * (1 - ambient))
        renderer.set_blend_mode('normal')
        renderer.draw_rect(0, 0, renderer.width, renderer.height, (0, 0, 0, darkness_alpha), fill=True)

        # 2. For each light, draw its lit area using additive blending, but with desaturated colors
        renderer.set_blend_mode('add')
        for light in self.lights:
            if not light.visible:
                continue

            screen_pos = camera.world_to_screen(light.position)
            radius = light.range * camera.zoom
            if radius <= 0:
                continue

            # Desaturate the light color by mixing with white
            r, g, b = light.color
            # Mix with white based on saturation parameter
            if saturation < 1.0:
                gray = (r + g + b) / 3.0
                r = r * saturation + gray * (1 - saturation)
                g = g * saturation + gray * (1 - saturation)
                b = b * saturation + gray * (1 - saturation)

            # Scale intensity and apply light power
            alpha = int(255 * light.intensity * light_power * 0.8)  # 0.8 is a base factor, tune as needed

            # Convert to 0-255 range
            r8 = int(r * 255)
            g8 = int(g * 255)
            b8 = int(b * 255)

            # Draw a filled circle with soft edges? For simplicity, we use a solid circle.
            # A radial gradient would be better, but for now solid is okay.
            renderer.draw_circle(screen_pos.x, screen_pos.y, radius, (r8, g8, b8, alpha), fill=True)

        renderer.set_blend_mode('normal')

    def get_stats(self):
        """Return simple statistics."""
        visible_lights = sum(1 for l in self.lights if l.visible)
        visible_casters = sum(1 for c in self.casters if c.visible)
        return {
            'lights': len(self.lights),
            'visible_lights': visible_lights,
            'casters': len(self.casters),
            'visible_casters': visible_casters
        }
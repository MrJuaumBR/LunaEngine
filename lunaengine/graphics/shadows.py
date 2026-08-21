"""
shadows.py – Lightweight real‑time shadow system for LunaEngine.

Provides:
- LightCaster: light source (position, colour, distance).
- ShadowCaster: object that casts shadows (circle/rect/polygon/texture).
- SCSManager: manager that renders shadows with fallback, optional gradient,
  optional blur, and debug overlays.
"""

import math
import pygame
from typing import List, Tuple, Dict, Union, Optional, Literal
from pygame import Rect, Vector2, Surface

from ..backend import OpenGLRenderer, Color, ColorKeys


# -----------------------------------------------------------------------------
# Unit conversion helpers (optional)
# -----------------------------------------------------------------------------

def pixel_to_centimeter(pixels: Union[int, float], dpi: int = 96) -> Union[int, float]:
    return (pixels / dpi) * 2.54

def centimeter_to_pixel(centimeters: Union[int, float], dpi: int = 96) -> Union[int, float]:
    return (centimeters * 2.54) * dpi

def meter_to_pixel(meters: Union[int, float], dpi: int = 96) -> Union[int, float]:
    return centimeter_to_pixel(meters * 100, dpi)


# -----------------------------------------------------------------------------
# LightCaster – light source
# -----------------------------------------------------------------------------

class LightCaster:
    """A light source that illuminates ShadowCasters and casts shadows."""

    def __init__(
        self,
        position: Tuple[float, float],
        shape: Literal['point', 'circle', 'rect'],
        color_key: Union[ColorKeys, List[Tuple[int, int, int, float]], List[Color]],
        brightness: float = 8.0,
        distance: float = 16.0,
        size: Optional[Union[float, Tuple[float, float]]] = None
    ):
        self.x, self.y = position
        self.shape = shape
        self.color_key = self._assert_color_key(color_key)
        self.brightness = brightness
        self.distance = distance
        self.size = size   # for area lights (not used in simple version)

    def _assert_color_key(self, key):
        if isinstance(key, ColorKeys):
            return key
        elif isinstance(key, list):
            return ColorKeys(key)
        else:
            raise TypeError("Light colour must be ColorKeys or list of colours")


# -----------------------------------------------------------------------------
# ShadowCaster – object that casts shadows
# -----------------------------------------------------------------------------

class ShadowCaster:
    """An object that casts a shadow when illuminated by a LightCaster."""

    x: Union[int, float]
    y: Union[int, float]
    shape: Literal['rect', 'circle', 'polygon', 'texture']
    color_key: ColorKeys
    size: Union[Rect, Tuple[int, int], Tuple[float, float], None]
    alpha_factor: float
    shadow_depth: float
    shadow_spread: float

    @property
    def position(self) -> Union[Tuple[int, int], Tuple[float, float]]:
        return self.x, self.y

    def __init__(
        self,
        position: Union[Vector2, Rect, Tuple[int, int], Tuple[float, float]],
        shape: Literal['rect', 'circle', 'polygon', 'texture'],
        color_key: Union[ColorKeys, List[Tuple[int, int, int, float]], List[Color]],
        size: Optional[Union[Rect, Tuple[int, int], Tuple[float, float]]] = None,
        alpha_factor: float = 0.6,
        shadow_depth: float = 1.0,
        shadow_spread: float = 1.0
    ):
        if isinstance(position, Vector2):
            self.x, self.y = position.x, position.y
        elif isinstance(position, Rect):
            self.x, self.y = position.x, position.y
        elif isinstance(position, tuple):
            self.x, self.y = position

        self.shape = shape
        self.size = size
        self.alpha_factor = alpha_factor
        self.shadow_depth = shadow_depth
        self.shadow_spread = shadow_spread
        self.color_key = self.assert_color_key(color_key)

    def assert_color_key(self, to_assert: Union[ColorKeys, List[Tuple[int, int, int, float]], List[Color]]) -> ColorKeys:
        if isinstance(to_assert, ColorKeys):
            to_assert.set_alpha_factor(self.alpha_factor)
            return to_assert
        elif isinstance(to_assert, list):
            return ColorKeys(to_assert, alpha_factor=self.alpha_factor)
        else:
            raise TypeError

    def compute_shadow_polygon(self, lx: float, ly: float, max_dist: float) -> List[Tuple[float, float]]:
        """
        Return the shadow polygon vertices for this caster.
        The actual length is max_dist * self.shadow_depth.
        The angular spread is multiplied by self.shadow_spread.
        """
        dx = self.x - lx
        dy = self.y - ly
        dist = math.hypot(dx, dy)
        if dist < 0.001:
            return []

        effective_max = max_dist * self.shadow_depth
        if effective_max <= 0:
            return []

        # Normalized direction from light to object
        nx = dx / dist
        ny = dy / dist

        if self.shape == 'circle':
            radius = self.size if isinstance(self.size, (int, float)) else 10.0
            # Base tangent angle
            base_angle = math.asin(min(1.0, radius / dist))
            # Apply spread multiplier (clamp to avoid flipping)
            angle = min(base_angle * self.shadow_spread, math.pi / 2 - 0.001)
            # Tangent points on the circle
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            t1x = self.x + radius * (nx * cos_a - ny * sin_a)
            t1y = self.y + radius * (nx * sin_a + ny * cos_a)
            t2x = self.x + radius * (nx * cos_a + ny * sin_a)
            t2y = self.y + radius * (-nx * sin_a + ny * cos_a)

            def extend(px, py):
                dx2 = px - lx
                dy2 = py - ly
                d2 = math.hypot(dx2, dy2)
                if d2 < 0.001:
                    return px, py
                factor = effective_max / d2
                return lx + dx2 * factor, ly + dy2 * factor

            p1 = extend(t1x, t1y)
            p2 = extend(t2x, t2y)
            return [(t1x, t1y), p1, p2, (t2x, t2y)]

        elif self.shape == 'rect':
            if isinstance(self.size, (tuple, list)) and len(self.size) == 2:
                w, h = self.size
            else:
                w, h = 20, 20
            # Four corners (center at self.x, self.y)
            corners = [
                (self.x - w/2, self.y - h/2),
                (self.x + w/2, self.y - h/2),
                (self.x + w/2, self.y + h/2),
                (self.x - w/2, self.y + h/2)
            ]

            # Find the two extreme corners relative to the light direction
            # by projecting onto the perpendicular axis.
            perp_x = -ny
            perp_y = nx
            vals = []
            for cx, cy in corners:
                vx = cx - lx
                vy = cy - ly
                perp_val = vx * perp_x + vy * perp_y
                vals.append(perp_val)

            # Indices of min and max perpendicular values
            min_idx = min(range(4), key=lambda i: vals[i])
            max_idx = max(range(4), key=lambda i: vals[i])
            c1 = corners[min_idx]
            c2 = corners[max_idx]

            def project(cx, cy):
                vx = cx - lx
                vy = cy - ly
                d = math.hypot(vx, vy)
                if d < 0.001:
                    return cx, cy
                factor = effective_max / d
                return lx + vx * factor, ly + vy * factor

            p1 = project(c1[0], c1[1])
            p2 = project(c2[0], c2[1])
            # Order: c1, p1, p2, c2 (convex)
            return [(c1[0], c1[1]), p1, p2, (c2[0], c2[1])]

        else:
            # Fallback for polygon/texture – not yet supported, return empty
            return []


# -----------------------------------------------------------------------------
# SCSManager – master controller
# -----------------------------------------------------------------------------

class SCSManager:
    """
    Manages all lights and shadow casters. Renders shadows with fallback,
    optional gradient (per‑polygon), optional blur, and debug overlays.
    """

    def __init__(self, engine: 'LunaEngine'):  # forward reference, no import needed
        self.engine = engine
        self.casters: List[ShadowCaster] = []
        self.lights: List[LightCaster] = []
        self.fallback_alpha = 0.2
        self.enabled = True          # master on/off switch
        self.profiler_enabled = True # record render times?
        self.shadow_blur = 0.0       # blur intensity (0 = no blur)
        self.use_gradient = False    # default to uniform alpha (faster)

    def add_shadow(
        self,
        position,
        shape,
        color_key,
        size=None,
        alpha_factor: float = 0.6,
        shadow_depth: float = 1.0,
        shadow_spread: float = 1.0
    ) -> ShadowCaster:
        s = ShadowCaster(
            position, shape, color_key, size,
            alpha_factor=alpha_factor,
            shadow_depth=shadow_depth,
            shadow_spread=shadow_spread
        )
        self.casters.append(s)
        return s

    def add_light(self, position, shape, color_key, brightness: float = 8.0, distance: float = 16.0, size=None) -> LightCaster:
        l = LightCaster(position, shape, color_key, brightness, distance, size)
        self.lights.append(l)
        return l

    def _draw_caster(self, caster: ShadowCaster, renderer: OpenGLRenderer, color: Color):
        if caster.shape == 'circle':
            radius = caster.size if isinstance(caster.size, (int, float)) else 10
            renderer.draw_circle(caster.x, caster.y, radius, color, fill=True)
        elif caster.shape == 'rect':
            if isinstance(caster.size, (tuple, list)) and len(caster.size) == 2:
                w, h = caster.size
            else:
                w, h = 20, 20
            renderer.draw_rect(caster.x - w/2, caster.y - h/2, w, h, color, fill=True)

    def render(self, renderer: OpenGLRenderer):
        """
        Renders all shadows in two passes:
          1. Fallback ambient shadow (low alpha) for every caster.
          2. Per‑light shadow polygons with either:
             - uniform alpha (if use_gradient is False)
             - linear gradient (if use_gradient is True)
        If engine.debug_enabled is True, also draws debug overlays.
        If shadow_blur > 0, shadows are rendered off‑screen, blurred, then composited.
        """
        if not self.enabled:
            return

        # Start profiling if available
        if self.profiler_enabled and hasattr(self.engine, 'performance_monitor'):
            self.engine.performance_monitor.start_timer("shadows_render")

        # Prepare blur surface if needed
        blur_surface = None
        old_target = None
        if self.shadow_blur > 0:
            # Create an offscreen surface with alpha
            blur_surface = pygame.Surface((renderer.width, renderer.height), pygame.SRCALPHA, 32)
            blur_surface.fill((0, 0, 0, 0))
            old_target = renderer.get_surface()
            renderer.set_surface(blur_surface)

        # 1. Fallback: draw all casters with low alpha (ambient shadow)
        for caster in self.casters:
            col = caster.color_key.avg
            col.a *= self.fallback_alpha
            self._draw_caster(caster, renderer, col)

        # 2. Light shadows
        for light in self.lights:
            light_color = light.color_key.avg
            for caster in self.casters:
                dx = caster.x - light.x
                dy = caster.y - light.y
                dist = math.hypot(dx, dy)
                if dist > light.distance:
                    continue
                vertices = caster.compute_shadow_polygon(light.x, light.y, light.distance)
                if not vertices:
                    continue

                # Alpha: fades with distance, scaled by caster.alpha_factor
                alpha = (1.0 - dist / light.distance) * caster.alpha_factor
                alpha = max(0.0, min(1.0, alpha))

                if self.use_gradient:
                    # Build gradient colors: near (full alpha) -> far (alpha=0)
                    r, g, b = light_color.r, light_color.g, light_color.b
                    grad_colors = [
                        (r, g, b, alpha * light_color.a),
                        (r, g, b, 0.0)
                    ]

                    # Compute gradient angle: direction from light to caster center
                    # We want the gradient to go from object (near) to far end.
                    # The angle should point from the object toward the far end.
                    # That's the direction from light to caster center (dx, dy).
                    angle_rad = math.atan2(dy, dx)   # dy, dx because atan2(y, x)
                    # For the renderer's gradient, 0° = right, 90° = down.
                    # We want the fade to go from near to far; the far direction is the same as
                    # the vector from light to caster, so we use that angle directly.
                    angle_deg = math.degrees(angle_rad)

                    style = {
                        'gradient': grad_colors,
                        'gradient_type': 'linear',
                        'gradient_angle': angle_deg
                    }
                    renderer.draw_polygon(vertices, style=style, fill=True)
                else:
                    # Uniform fill: use the computed alpha
                    shadow_col = (light_color.r, light_color.g, light_color.b, alpha * light_color.a)
                    renderer.draw_polygon(vertices, shadow_col, fill=True)

        # ----- Debug visualization (only if debug is enabled) -----
        if self.engine.debug_enabled:
            # Draw casters as green dots
            for caster in self.casters:
                renderer.draw_circle(caster.x, caster.y, 4, Color(0, 255, 0, 255), fill=True)

            # Draw lights as blue dots + distance circle
            for light in self.lights:
                renderer.draw_circle(light.x, light.y, 6, Color(0, 0, 255, 255), fill=True)
                renderer.draw_circle(
                    light.x, light.y, light.distance,
                    Color(255, 255, 0, 50), fill=False, border_width=1
                )

            # Draw shadow polygon outlines in red for all light–caster pairs in range
            for light in self.lights:
                for caster in self.casters:
                    dx = caster.x - light.x
                    dy = caster.y - light.y
                    dist = math.hypot(dx, dy)
                    if dist > light.distance:
                        continue
                    vertices = caster.compute_shadow_polygon(light.x, light.y, light.distance)
                    if not vertices:
                        continue
                    n = len(vertices)
                    for i in range(n):
                        x1, y1 = vertices[i]
                        x2, y2 = vertices[(i + 1) % n]
                        renderer.draw_line(x1, y1, x2, y2, Color(255, 0, 0, 255), width=2)

        # ---- Blur and composite ----
        if self.shadow_blur > 0 and blur_surface is not None:
            # Restore main framebuffer
            renderer.set_surface(old_target)

            # Apply blur to the shadow surface using a simple box blur
            if self.shadow_blur > 0.5:
                factor = max(2, int(1 / self.shadow_blur * 4))
                factor = min(max(2, factor), 16)  # clamp

                w, h = blur_surface.get_size()
                small_w = max(1, w // factor)
                small_h = max(1, h // factor)

                small = pygame.transform.smoothscale(blur_surface, (small_w, small_h))
                blurred = pygame.transform.smoothscale(small, (w, h))
                blur_surface = blurred

            # Blit the blurred shadow surface onto the main framebuffer
            renderer.blit(blur_surface, (0, 0))

        if self.profiler_enabled and hasattr(self.engine, 'performance_monitor'):
            self.engine.performance_monitor.end_timer("shadows_render")

    def get_stats(self):
        """Return simple statistics."""
        return {
            'lights': len(self.lights),
            'casters': len(self.casters),
            'fallback_alpha': self.fallback_alpha,
            'shadow_blur': self.shadow_blur,
            'use_gradient': self.use_gradient
        }
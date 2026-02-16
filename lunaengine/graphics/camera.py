"""
Camera System - Advanced 2D Camera with Smooth Movement, Effects, and Parallax

LOCATION: lunaengine/graphics/camera.py

DESCRIPTION:
A flexible, high‑performance 2D camera system for LunaEngine. Features:
- Unified coordinate system: camera.position = center of viewport
- Strategy‑based follow modes (extensible via FollowStrategy)
- Smooth interpolation with multiple easing types
- Constraints (zoom limits, world boundaries)
- Stackable effects (shake, trauma, fade, etc.)
- Optimised parallax backgrounds with tile support

LIBRARIES USED:
- pygame: Vector2, Rect, Surface operations
- numpy: Random for shake, vectorized operations (optional)
- abc, enum, dataclasses, typing
"""

import pygame
import math
import numpy as np
from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Tuple, Callable, List, TYPE_CHECKING, Union, Dict, Any

if TYPE_CHECKING:
    from lunaengine.core import Scene
    from lunaengine.core import LunaEngine

# ----------------------------------------------------------------------
# Enums
# ----------------------------------------------------------------------

class CameraMode(Enum):
    """Legacy follow modes – kept for backward compatibility.
       Internally mapped to FollowStrategy instances."""
    FIXED = "fixed"
    FOLLOW = "follow"
    PLATFORMER = "platformer"
    TOPDOWN = "topdown"


class CameraShakeType(Enum):
    """Type of camera shake effect."""
    POSITIONAL = "positional"
    ROTATIONAL = "rotational"
    TRAUMA = "trauma"


class InterpolationType(Enum):
    """Easing functions for smooth camera movement."""
    LINEAR = "linear"
    SMOOTHSTEP = "smoothstep"
    QUADRATIC_IN = "quadratic_in"
    QUADRATIC_OUT = "quadratic_out"
    QUADRATIC_IN_OUT = "quadratic_in_out"
    CUBIC_IN = "cubic_in"
    CUBIC_OUT = "cubic_out"
    CUBIC_IN_OUT = "cubic_in_out"


# ----------------------------------------------------------------------
# Interpolation helpers
# ----------------------------------------------------------------------

def _interpolate_linear(start: float, end: float, t: float) -> float:
    return start * (1 - t) + end * t


def _interpolate_smoothstep(start: float, end: float, t: float) -> float:
    t = t * t * (3 - 2 * t)
    return start * (1 - t) + end * t


def _interpolate_quadratic_in(start: float, end: float, t: float) -> float:
    return start + (end - start) * t * t


def _interpolate_quadratic_out(start: float, end: float, t: float) -> float:
    return start + (end - start) * (t * (2 - t))


def _interpolate_quadratic_in_out(start: float, end: float, t: float) -> float:
    t *= 2
    if t < 1:
        return start + (end - start) * 0.5 * t * t
    t -= 1
    return start + (end - start) * 0.5 * (1 - t * t * t * t + 2 * t * t * t + t * t)


def _interpolate_cubic_in(start: float, end: float, t: float) -> float:
    return start + (end - start) * t * t * t


def _interpolate_cubic_out(start: float, end: float, t: float) -> float:
    t -= 1
    return start + (end - start) * (t * t * t + 1)


def _interpolate_cubic_in_out(start: float, end: float, t: float) -> float:
    t *= 2
    if t < 1:
        return start + (end - start) * 0.5 * t * t * t
    t -= 2
    return start + (end - start) * 0.5 * (t * t * t + 2)


_INTERPOLATION_FUNCS = {
    InterpolationType.LINEAR: _interpolate_linear,
    InterpolationType.SMOOTHSTEP: _interpolate_smoothstep,
    InterpolationType.QUADRATIC_IN: _interpolate_quadratic_in,
    InterpolationType.QUADRATIC_OUT: _interpolate_quadratic_out,
    InterpolationType.QUADRATIC_IN_OUT: _interpolate_quadratic_in_out,
    InterpolationType.CUBIC_IN: _interpolate_cubic_in,
    InterpolationType.CUBIC_OUT: _interpolate_cubic_out,
    InterpolationType.CUBIC_IN_OUT: _interpolate_cubic_in_out,
}


def interpolate(start: Union[float, pygame.Vector2],
                end: Union[float, pygame.Vector2],
                t: float,
                itype: InterpolationType = InterpolationType.LINEAR) -> Union[float, pygame.Vector2]:
    """Interpolate between start and end using the specified easing function."""
    func = _INTERPOLATION_FUNCS[itype]
    if isinstance(start, (float, int)) and isinstance(end, (float, int)):
        return func(start, end, t)
    if isinstance(start, pygame.Vector2) and isinstance(end, pygame.Vector2):
        return pygame.Vector2(func(start.x, end.x, t),
                              func(start.y, end.y, t))
    raise TypeError("start and end must both be float/int or pygame.Vector2")


# ----------------------------------------------------------------------
# Follow Strategies (extensible)
# ----------------------------------------------------------------------

class FollowStrategy(ABC):
    """Abstract base class for camera follow behaviours."""
    @abstractmethod
    def get_target_position(self, camera: 'Camera', dt: float) -> pygame.Vector2:
        """Return the desired world position of the camera (center)."""
        pass


class SimpleFollow(FollowStrategy):
    """Follow the target's world position directly."""
    def get_target_position(self, camera: 'Camera', dt: float) -> pygame.Vector2:
        return camera._get_target_position()


class FixedFollow(FollowStrategy):
    """Keep the camera at a fixed world position, ignoring the target."""
    def __init__(self, fixed_position: Union[Tuple[float, float], pygame.Vector2]):
        self.fixed_position = pygame.Vector2(fixed_position)

    def get_target_position(self, camera: 'Camera', dt: float) -> pygame.Vector2:
        return self.fixed_position


class PlatformerFollow(FollowStrategy):
    """
    Platformer-style camera with a deadzone in screen space.
    The camera moves only when the target leaves the deadzone rectangle.
    """
    def __init__(self, deadzone_rect: Optional[pygame.Rect] = None):
        # Default deadzone: 200x150 centered on screen
        self.deadzone = deadzone_rect or pygame.Rect(0, 0, 200, 150)

    def get_target_position(self, camera: 'Camera', dt: float) -> pygame.Vector2:
        target_screen = camera.world_to_screen(camera._get_target_position())
        # Deadzone is defined in screen coordinates; we keep it centered on the viewport.
        half_w = self.deadzone.width / 2
        half_h = self.deadzone.height / 2
        center = pygame.Vector2(camera.viewport_width / 2, camera.viewport_height / 2)

        delta = target_screen - center
        move_x = 0.0
        move_y = 0.0

        if abs(delta.x) > half_w:
            move_x = delta.x - (half_w if delta.x > 0 else -half_w)
        if abs(delta.y) > half_h:
            move_y = delta.y - (half_h if delta.y > 0 else -half_h)

        # Convert screen movement (pixels) to world movement (world units)
        world_move = pygame.Vector2(move_x, move_y) / camera.zoom
        return camera._position + world_move


class TopDownFollow(FollowStrategy):
    """
    Top-down RPG style camera with look‑ahead based on target velocity/direction.
    """
    def __init__(self, lead_factor: float = 0.3):
        self.lead_factor = lead_factor

    def get_target_position(self, camera: 'Camera', dt: float) -> pygame.Vector2:
        target_pos = camera._get_target_position()
        lead_offset = pygame.Vector2(0, 0)

        if camera.target is not None:
            vel = None
            if hasattr(camera.target, 'velocity'):
                vel = camera.target.velocity
            elif hasattr(camera.target, 'direction'):
                vel = camera.target.direction

            if vel is not None:
                if isinstance(vel, (list, tuple, np.ndarray)):
                    lead_offset = pygame.Vector2(vel[0], vel[1]) * 50 * self.lead_factor
                elif isinstance(vel, pygame.Vector2):
                    lead_offset = vel * 50 * self.lead_factor

        return target_pos + lead_offset


# ----------------------------------------------------------------------
# Camera Constraints
# ----------------------------------------------------------------------

@dataclass
class CameraConstraints:
    """Limits applied to camera movement and zoom."""
    min_zoom: float = 0.1
    max_zoom: float = 10.0
    bounds: Optional[pygame.Rect] = None          # world rectangle the camera must stay inside
    rotation_range: Tuple[float, float] = (-180.0, 180.0)


# ----------------------------------------------------------------------
# Camera Effects (stackable)
# ----------------------------------------------------------------------

class CameraEffect(ABC):
    """Base class for temporary camera effects (shake, fade, flash, etc.)."""
    @abstractmethod
    def update(self, dt: float) -> bool:
        """Update effect state. Return True if still active, False when finished."""
        pass

    @abstractmethod
    def apply(self, camera: 'Camera') -> None:
        """Modify the camera's offset, rotation, zoom, etc."""
        pass


class ShakeEffect(CameraEffect):
    """Positional or rotational shake with intensity decay."""
    def __init__(self,
                 intensity: float = 1.0,
                 duration: float = 0.5,
                 shake_type: CameraShakeType = CameraShakeType.POSITIONAL):
        self.initial_intensity = intensity
        self.intensity = intensity
        self.duration = duration
        self.time_left = duration
        self.shake_type = shake_type
        self.offset = pygame.Vector2(0, 0)
        self.rotation_offset = 0.0

    def update(self, dt: float) -> bool:
        self.time_left -= dt
        if self.time_left <= 0:
            return False
        # Linear decay
        self.intensity = self.initial_intensity * (self.time_left / self.duration)
        return True

    def apply(self, camera: 'Camera') -> None:
        if self.shake_type == CameraShakeType.POSITIONAL:
            self.offset.x = (np.random.random() - 0.5) * 2 * self.intensity * 20
            self.offset.y = (np.random.random() - 0.5) * 2 * self.intensity * 20
        elif self.shake_type == CameraShakeType.ROTATIONAL:
            self.rotation_offset = (np.random.random() - 0.5) * 2 * self.intensity * 5
        elif self.shake_type == CameraShakeType.TRAUMA:
            self.offset.x = (np.random.random() - 0.5) * 2 * self.intensity * 20
            self.offset.y = (np.random.random() - 0.5) * 2 * self.intensity * 20
            self.rotation_offset = (np.random.random() - 0.5) * 2 * self.intensity * 5

        camera.offset += self.offset
        camera.rotation_offset += self.rotation_offset


class TraumaEffect(CameraEffect):
    """Trauma‑based shake – intensity scales with trauma^2."""
    def __init__(self, trauma: float = 1.0, decay_rate: float = 1.5):
        self.trauma = trauma
        self.decay_rate = decay_rate

    def update(self, dt: float) -> bool:
        self.trauma = max(0.0, self.trauma - dt * self.decay_rate)
        return self.trauma > 0.0

    def apply(self, camera: 'Camera') -> None:
        intensity = self.trauma ** 2
        camera.offset.x = (np.random.random() - 0.5) * 2 * intensity * 20
        camera.offset.y = (np.random.random() - 0.5) * 2 * intensity * 20
        camera.rotation_offset = (np.random.random() - 0.5) * 2 * intensity * 5


# ----------------------------------------------------------------------
# Parallax System (optimised, works with unified camera)
# ----------------------------------------------------------------------

class ParallaxLayer:
    """A single parallax layer with tile support."""
    def __init__(self,
                 surface: pygame.Surface,
                 speed_factor: float,
                 tile_mode: bool = True,
                 offset: Tuple[float, float] = (0, 0)):
        self.surface = surface
        self.speed_factor = speed_factor
        self.tile_mode = tile_mode
        self.offset = pygame.Vector2(offset)
        self._texture_size = surface.get_size()
        self._world_offset = pygame.Vector2(0, 0)   # world position of layer's origin

    def update(self, camera_position: pygame.Vector2, dt: float):
        """Update the layer's world offset based on camera position."""
        # speed_factor = 0 -> layer is fixed in world at self.offset
        # speed_factor = 1 -> layer moves exactly with the camera (world offset = camera_position)
        self._world_offset = self.offset - camera_position * (1 - self.speed_factor)

    def render(self, camera: 'Camera', renderer) -> None:
        """Render the layer using the provided renderer."""
        # Convert world offset to screen position
        screen_pos = camera.world_to_screen(self._world_offset)
        tex_w, tex_h = self._texture_size

        if self.tile_mode:
            # Tile to cover the entire viewport
            view_w, view_h = camera.viewport_width, camera.viewport_height

            # Calculate tile range with a margin of 1 tile
            start_x = int(screen_pos.x // tex_w) - 1
            end_x = int((screen_pos.x + view_w) // tex_w) + 2
            start_y = int(screen_pos.y // tex_h) - 1
            end_y = int((screen_pos.y + view_h) // tex_h) + 2

            for ty in range(start_y, end_y):
                for tx in range(start_x, end_x):
                    x = screen_pos.x + tx * tex_w
                    y = screen_pos.y + ty * tex_h
                    # Cull off‑screen tiles (simple check)
                    if x + tex_w < 0 or x > view_w or y + tex_h < 0 or y > view_h:
                        continue
                    self._draw_surface(renderer, self.surface, int(x), int(y))
        else:
            # Single copy
            self._draw_surface(renderer, self.surface, int(screen_pos.x), int(screen_pos.y))

    def _draw_surface(self, renderer, surface: pygame.Surface, x: int, y: int):
        """Renderer‑agnostic surface drawing."""
        if hasattr(renderer, 'draw_surface'):
            renderer.draw_surface(surface, x, y)
        elif hasattr(renderer, 'render_surface'):
            renderer.render_surface(surface, x, y)
        elif hasattr(renderer, 'get_surface'):
            # Fallback: blit directly onto the renderer's target surface
            target = renderer.get_surface()
            target.blit(surface, (x, y))


class ParallaxBackground:
    """Collection of parallax layers with optional caching."""
    def __init__(self, camera: 'Camera'):
        self.camera = camera
        self.layers: List[ParallaxLayer] = []
        self.enabled = True

    def add_layer(self,
                  surface: pygame.Surface,
                  speed_factor: float,
                  tile_mode: bool = True,
                  offset: Tuple[float, float] = (0, 0)) -> ParallaxLayer:
        """Add a new layer and return it."""
        layer = ParallaxLayer(surface, speed_factor, tile_mode, offset)
        self.layers.append(layer)
        return layer

    def remove_layer(self, layer: ParallaxLayer):
        """Remove a layer if present."""
        if layer in self.layers:
            self.layers.remove(layer)

    def clear_layers(self):
        """Remove all layers."""
        self.layers.clear()

    def update(self, dt: float):
        """Update all layers."""
        if not self.enabled:
            return
        for layer in self.layers:
            layer.update(self.camera._position, dt)

    def render(self, renderer) -> bool:
        """Render all layers in order (back to front)."""
        if not self.enabled or not self.layers:
            return False

        # Sort by speed_factor (slower layers = background first)
        sorted_layers = sorted(self.layers, key=lambda l: l.speed_factor)
        for layer in sorted_layers:
            layer.render(self.camera, renderer)
        return True


# ----------------------------------------------------------------------
# Camera - Main Class
# ----------------------------------------------------------------------

class Camera:
    """
    Advanced 2D Camera with unified coordinate system (position = viewport center).
    Supports multiple follow strategies, constraints, effects, and parallax.
    """

    def __init__(self, scene: 'Scene', width: int, height: int):
        self.scene = scene
        self.engine = self.scene.engine
        self.renderer = self.engine.renderer
        self.viewport_width = width
        self.viewport_height = height

        # ----- Core state -----
        self._position = pygame.Vector2(0.0, 0.0)      # world position of viewport center
        self.target_position = pygame.Vector2(0.0, 0.0)
        self.zoom = 1.0
        self.target_zoom = 1.0
        self.rotation = 0.0
        self.rotation_offset = 0.0

        # ----- Follow target & strategy -----
        self.target = None
        self._follow_strategy: FollowStrategy = SimpleFollow()
        self._mode = CameraMode.FOLLOW   # kept for backward compatibility

        # ----- Interpolation -----
        self.smooth_speed = 0.1
        self.interpolation_type = InterpolationType.LINEAR

        # ----- Constraints -----
        self.constraints = CameraConstraints()

        # ----- Effects -----
        self._effects: List[CameraEffect] = []
        self.offset = pygame.Vector2(0.0, 0.0)   # cumulative offset from effects

        # ----- Legacy attributes (used by old code, now mapped) -----
        self.deadzone = pygame.Rect(0, 0, 200, 150)
        self.deadzone.center = (width // 2, height // 2)
        self.lead_factor = 0.3
        self.bounds = None
        self.limit_enabled = True

        # ----- Parallax -----
        self.parallax = ParallaxBackground(self)

        # ----- Callbacks -----
        self.on_shake_complete: Optional[Callable] = None

        # ----- Internal: viewport rect in world units -----
        self._viewport_rect = pygame.Rect(0, 0, width, height)

    # ------------------------------------------------------------------
    # Properties (backward compatible)
    # ------------------------------------------------------------------

    @property
    def position(self) -> pygame.Vector2:
        """Camera position with active shake offset applied."""
        return self._position + self.offset

    @position.setter
    def position(self, value):
        """Set the base camera position (center of viewport)."""
        if isinstance(value, (list, tuple, np.ndarray)):
            self._position = pygame.Vector2(value[0], value[1])
        elif isinstance(value, pygame.Vector2):
            self._position = value
        else:
            raise ValueError("Position must be tuple, list, numpy array or pygame.Vector2")

    @property
    def base_position(self) -> pygame.Vector2:
        """Base camera position without shake offset."""
        return self._position

    @property
    def mode(self) -> CameraMode:
        """Legacy: get current follow mode (maps to strategy)."""
        return self._mode

    @mode.setter
    def mode(self, value: CameraMode):
        """Legacy: set follow mode and update strategy accordingly."""
        self._mode = value
        if value == CameraMode.FIXED:
            self._follow_strategy = FixedFollow(self._position)
        elif value == CameraMode.FOLLOW:
            self._follow_strategy = SimpleFollow()
        elif value == CameraMode.PLATFORMER:
            self._follow_strategy = PlatformerFollow(self.deadzone)
        elif value == CameraMode.TOPDOWN:
            self._follow_strategy = TopDownFollow(self.lead_factor)

    @property
    def viewport_rect(self) -> pygame.Rect:
        """World rectangle visible through the camera (topleft in world coordinates)."""
        return self._viewport_rect

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_target(self, target, mode: Optional[CameraMode] = None):
        """
        Set the camera target. If mode is provided, it updates the follow strategy.
        """
        self.target = target
        if mode is not None:
            self.mode = mode

    def set_follow_strategy(self, strategy: FollowStrategy):
        """Set a custom follow strategy."""
        self._follow_strategy = strategy
        # Also update legacy mode based on strategy type (optional)
        if isinstance(strategy, SimpleFollow):
            self._mode = CameraMode.FOLLOW
        elif isinstance(strategy, FixedFollow):
            self._mode = CameraMode.FIXED
        elif isinstance(strategy, PlatformerFollow):
            self._mode = CameraMode.PLATFORMER
        elif isinstance(strategy, TopDownFollow):
            self._mode = CameraMode.TOPDOWN

    def set_bounds(self, bounds: pygame.Rect):
        """Set world boundaries (legacy)."""
        self.bounds = bounds
        self.constraints.bounds = bounds

    def set_zoom(self, zoom: float, smooth: bool = True):
        """Set target zoom level."""
        self.target_zoom = max(self.constraints.min_zoom, min(zoom, self.constraints.max_zoom))
        if not smooth:
            self.zoom = self.target_zoom

    def shake(self, intensity: float = 1.0, duration: float = 0.5,
              shake_type: CameraShakeType = CameraShakeType.POSITIONAL):
        """Start a camera shake effect."""
        effect = ShakeEffect(intensity, duration, shake_type)
        self.add_effect(effect)

    def add_trauma(self, amount: float):
        """Add trauma (if a TraumaEffect exists, increase it; otherwise create one)."""
        # Find existing trauma effect
        for e in self._effects:
            if isinstance(e, TraumaEffect):
                e.trauma = min(1.0, e.trauma + amount)
                return
        # No trauma effect yet
        self.add_effect(TraumaEffect(trauma=amount))

    def add_effect(self, effect: CameraEffect):
        """Add a new camera effect (will be updated/removed automatically)."""
        self._effects.append(effect)

    def remove_effect(self, effect: CameraEffect):
        """Remove a specific effect."""
        if effect in self._effects:
            self._effects.remove(effect)

    def clear_effects(self):
        """Remove all active effects."""
        self._effects.clear()

    # ------------------------------------------------------------------
    # Core update
    # ------------------------------------------------------------------

    def update(self, dt: float):
        """Update camera position, zoom, effects, and parallax."""
        # 1. Update follow target position
        if self.target is not None:
            self.target_position = self._follow_strategy.get_target_position(self, dt)

        # 2. Smooth movement
        self._apply_smooth_movement(dt)

        # 3. Smooth zoom
        self._apply_smooth_zoom(dt)

        # 4. Apply effects (shake, trauma, etc.)
        self._update_effects(dt)

        # 5. Apply constraints (world bounds)
        self._apply_constraints()

        # 6. Update viewport rect (world topleft)
        self._update_viewport_rect()

        # 7. Update parallax layers
        self.parallax.update(dt)

        # 8. Notify renderer of new camera position
        self._update_renderer_camera_position()

    def _apply_smooth_movement(self, dt: float):
        """Interpolate _position towards target_position."""
        t = min(1.0, self.smooth_speed * dt * 60.0)
        self._position = interpolate(self._position, self.target_position, t, self.interpolation_type)

    def _apply_smooth_zoom(self, dt: float):
        """Interpolate zoom towards target_zoom."""
        if abs(self.target_zoom - self.zoom) > 0.001:
            t = min(1.0, self.smooth_speed * dt * 60.0)
            self.zoom = interpolate(self.zoom, self.target_zoom, t, InterpolationType.LINEAR)

    def _update_effects(self, dt: float):
        """Update all active effects and remove finished ones."""
        self.offset = pygame.Vector2(0, 0)
        self.rotation_offset = 0.0

        finished = []
        for effect in self._effects:
            if not effect.update(dt):
                finished.append(effect)
            else:
                effect.apply(self)

        for effect in finished:
            self._effects.remove(effect)

    def _apply_constraints(self):
        """Apply world bounds and zoom limits."""
        # Zoom limits are enforced in set_zoom
        if self.constraints.bounds and self.limit_enabled:
            bounds = self.constraints.bounds
            half_w = (self.viewport_width / 2) / self.zoom
            half_h = (self.viewport_height / 2) / self.zoom

            min_x = bounds.left + half_w
            max_x = bounds.right - half_w
            min_y = bounds.top + half_h
            max_y = bounds.bottom - half_h

            if min_x > max_x:
                min_x = max_x = (bounds.left + bounds.right) / 2
            if min_y > max_y:
                min_y = max_y = (bounds.top + bounds.bottom) / 2

            self._position.x = np.clip(self._position.x, min_x, max_x)
            self._position.y = np.clip(self._position.y, min_y, max_y)
            self.target_position = self._position.copy()

    def _update_viewport_rect(self):
        """Recalculate viewport_rect based on current position and zoom."""
        half_w = (self.viewport_width / 2) / self.zoom
        half_h = (self.viewport_height / 2) / self.zoom
        self._viewport_rect = pygame.Rect(
            self._position.x - half_w,
            self._position.y - half_h,
            self.viewport_width / self.zoom,
            self.viewport_height / self.zoom
        )

    def _update_renderer_camera_position(self):
        """Push camera position to the renderer."""
        self.renderer.camera_position = self.position
        # If a separate UI renderer exists, set its position to zero
        if hasattr(self.engine, 'ui_renderer') and self.engine.ui_renderer != self.renderer:
            self.engine.ui_renderer.camera_position = pygame.Vector2(0, 0)

    # ------------------------------------------------------------------
    # Coordinate conversion (UNIFIED: camera.position = center)
    # ------------------------------------------------------------------

    def world_to_screen(self, world_pos: Union[Tuple[float, float], pygame.Vector2, List[float], np.ndarray]) -> pygame.Vector2:
        """Convert world coordinates to screen pixels (top‑left origin)."""
        if not isinstance(world_pos, pygame.Vector2):
            world_pos = pygame.Vector2(world_pos[0], world_pos[1])
        # screen = (world - viewport.topleft) * zoom
        return (world_pos - self._viewport_rect.topleft) * self.zoom

    def world_to_screen_list(self, world_positions: List, return_type: str = 'list'):
        """Batch conversion for lists of world positions."""
        if return_type == 'list':
            return [self.world_to_screen(p) for p in world_positions]
        elif return_type in ('nparray', 'ndarray'):
            return np.array([self.world_to_screen(p) for p in world_positions])
        else:
            raise ValueError("return_type must be 'list' or 'nparray'")

    def screen_to_world(self, screen_pos: Union[Tuple[float, float], pygame.Vector2, List[float], np.ndarray]) -> pygame.Vector2:
        """Convert screen pixel coordinates to world coordinates."""
        if not isinstance(screen_pos, pygame.Vector2):
            screen_pos = pygame.Vector2(screen_pos[0], screen_pos[1])
        # world = viewport.topleft + screen / zoom
        return self._viewport_rect.topleft + screen_pos / self.zoom

    def screen_to_world_list(self, screen_positions: List) -> List[pygame.Vector2]:
        """Batch conversion for lists of screen positions."""
        return [self.screen_to_world(p) for p in screen_positions]

    def screen_to_world_vector(self, screen_vec: Union[Tuple[float, float], pygame.Vector2]) -> pygame.Vector2:
        """Convert a screen vector (e.g., movement) to world vector (ignores viewport offset)."""
        if not isinstance(screen_vec, pygame.Vector2):
            screen_vec = pygame.Vector2(screen_vec[0], screen_vec[1])
        return screen_vec / self.zoom

    # ------------------------------------------------------------------
    # Size conversion utilities
    # ------------------------------------------------------------------

    def convert_size_zoom(self, size: Union[Tuple[float, float], List[float], float, pygame.Vector2]):
        """Scale a size from world units to screen pixels, or vice‑versa."""
        if isinstance(size, (tuple, list)):
            return (size[0] / self.zoom, size[1] / self.zoom)
        elif isinstance(size, (int, float, np.float32)):
            return size / self.zoom
        elif isinstance(size, pygame.Vector2):
            return size / self.zoom
        else:
            raise TypeError(f"size must be tuple, list, int, float, or pygame.Vector2\nIt is: {type(size)}")

    def convert_size_zoom_list(self, sizes: List, return_type: str = 'list'):
        """Batch version of convert_size_zoom."""
        if return_type == 'list':
            return [self.convert_size_zoom(s) for s in sizes]
        elif return_type in ('nparray', 'ndarray'):
            return np.array([self.convert_size_zoom(s) for s in sizes])
        else:
            raise ValueError("return_type must be 'list' or 'nparray'")

    # ------------------------------------------------------------------
    # Visibility and query
    # ------------------------------------------------------------------

    def get_visible_rect(self) -> pygame.Rect:
        """Alias for viewport_rect."""
        return self._viewport_rect

    def is_visible(self, world_pos: Union[Tuple[float, float], pygame.Vector2], margin: float = 0.0) -> bool:
        """Check if a world point is inside the viewport (plus optional margin)."""
        screen_pos = self.world_to_screen(world_pos)
        return (-margin <= screen_pos.x <= self.viewport_width + margin and
                -margin <= screen_pos.y <= self.viewport_height + margin)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_target_position(self) -> pygame.Vector2:
        """Extract the world position of the current target (if any)."""
        if self.target is None:
            return self._position

        if hasattr(self.target, 'rect'):
            return pygame.Vector2(self.target.rect.center)
        elif hasattr(self.target, 'position'):
            pos = self.target.position
            if isinstance(pos, (list, tuple, np.ndarray)):
                return pygame.Vector2(pos[0], pos[1])
            elif isinstance(pos, pygame.Vector2):
                return pos
            else:
                return pygame.Vector2(pos[0], pos[1])
        elif isinstance(self.target, dict):
            if 'x' in self.target and 'y' in self.target:
                return pygame.Vector2(self.target['x'], self.target['y'])
            elif 'position' in self.target:
                p = self.target['position']
                return pygame.Vector2(p[0], p[1])
        elif hasattr(self.target, '__len__') and len(self.target) >= 2:
            return pygame.Vector2(self.target[0], self.target[1])
        elif isinstance(self.target, pygame.Vector2):
            return self.target
        else:
            return self._position

    # ------------------------------------------------------------------
    # Parallax proxy methods
    # ------------------------------------------------------------------

    def add_parallax_layer(self, surface: pygame.Surface, speed_factor: float,
                           tile_mode: bool = True, offset: Tuple[float, float] = (0, 0)) -> ParallaxLayer:
        """Add a new parallax layer to the camera."""
        return self.parallax.add_layer(surface, speed_factor, tile_mode, offset)

    def remove_parallax_layer(self, layer: ParallaxLayer):
        """Remove a parallax layer."""
        self.parallax.remove_layer(layer)

    def clear_parallax_layers(self):
        """Remove all parallax layers."""
        self.parallax.clear_layers()

    def render_parallax(self, renderer) -> bool:
        """Render the parallax background."""
        return self.parallax.render(renderer)

    def enable_parallax(self, enabled: bool = True):
        """Enable/disable parallax rendering."""
        self.parallax.enabled = enabled

    def get_parallax_layer_count(self) -> int:
        """Number of active parallax layers."""
        return len(self.parallax.layers)
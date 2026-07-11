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

import pygame, math, random
import numpy as np
from enum import Enum
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Tuple, Callable, List, TYPE_CHECKING, Union, Dict, Any
from ..backend.opengl import OpenGLRenderer

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

@dataclass
class ParallaxSprite:
    """
    A single sprite inside a parallax layer.
    
    Attributes:
        surface: The image to draw.
        base_pos: World position relative to the layer's origin (in world units).
        scale: Uniform scale factor (1.0 = original size).
        color: RGB colour multiplier (1.0,1.0,1.0 = normal).
        alpha: Opacity (0.0 = transparent, 1.0 = opaque).
        angle: Rotation in degrees (0 = no rotation).
        oscillate_x: Sine wave amplitude for X movement (world units).
        oscillate_y: Sine wave amplitude for Y movement.
        oscillate_speed: Oscillation frequency (cycles per second).
        phase_offset: Initial phase offset (radians) – randomise for variety.
        brightness_pulse: Amplitude of brightness pulsation (0..1).
        brightness_speed: Pulsation speed (cycles per second).
    """
    surface: pygame.Surface
    base_pos: pygame.Vector2 = field(default_factory=lambda: pygame.Vector2(0,0))
    _cache: Dict[str, Tuple[float, float, Tuple[int, int, int]]]  = field(default_factory=dict, init=False, repr=False)
    scale: float = 1.0
    color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    alpha: float = 1.0
    angle: float = 0.0
    oscillate_x: float = 0.0
    oscillate_y: float = 0.0
    oscillate_speed: float = 1.0
    phase_offset: float = 0.0
    brightness_pulse: float = 0.0
    brightness_speed: float = 1.0
    wind_movement: bool = True
    wind_intensity: float = 0.0

    def __post_init__(self):
        self._cache = {}

    def get_animated_offset(self, time: float) -> pygame.Vector2:
        if self.wind_movement and self.wind_intensity > 0:
            dx = self.wind_intensity * math.sin(time * self.oscillate_speed * 2*math.pi + self.phase_offset)
        else:
            dx = self.oscillate_x * math.sin(time * self.oscillate_speed * 2*math.pi + self.phase_offset)
        dy = self.oscillate_y * math.sin(time * self.oscillate_speed * 2*math.pi + self.phase_offset)
        return pygame.Vector2(dx, dy)

    def get_current_brightness(self, time: float) -> float:
        """Return a brightness multiplier (0..1) pulsating over time."""
        if self.brightness_pulse <= 0:
            return 1.0
        # pulse from 0.5 to 1.5, then clamped? Better: from (1 - pulse) to (1 + pulse)
        t = math.sin(time * self.brightness_speed * 2*math.pi + self.phase_offset)
        return 1.0 + self.brightness_pulse * t
    
    def get_transformed_surface(self, size: Tuple[int, int], angle: float, colour: Tuple[float, float, float, float]) -> pygame.Surface:
        """
        Return a cached transformed version of the sprite surface.
        size: (width, height) in pixels after scaling
        angle: rotation in degrees
        colour: (r,g,b,a) multipliers (each 0..1)
        """
        key = (size, angle, colour)
        if key in self._cache:
            return self._cache[key]

        # Scale
        surf = pygame.transform.smoothscale(self.surface, size)
        # Rotate
        if angle != 0:
            surf = pygame.transform.rotate(surf, angle)
        # Colour modulate
        r,g,b,a = colour
        if (r,g,b) != (1.0,1.0,1.0):
            mod_surf = surf.copy()
            mod_surf.fill((int(r*255), int(g*255), int(b*255)), special_flags=pygame.BLEND_MULT)
            surf = mod_surf
        if a != 1.0:
            surf.set_alpha(int(a*255))

        self._cache[key] = surf
        return surf


class ParallaxLayer:
    """
    A scrollable layer that can contain:
      - A single tiled texture (simple & efficient)
      - A list of individual ParallaxSprites (flexible)
    
    If `tile_texture` is set, the layer ignores the sprite list and renders tiled.
    Otherwise, it renders the sprite list.
    """
    def __init__(self, speed: Tuple[float, float] = (1.0, 1.0),
                 repeat_x: bool = True, repeat_y: bool = True,
                 z_index: int = 0):
        """
        Args:
            speed: Scroll multiplier (1.0 = moves with camera, 0.0 = fixed in background)
            repeat_x, repeat_y: Only used for tiled texture mode.
            z_index: Render order (lower = behind).
        """
        self.speed = pygame.Vector2(speed[0], speed[1])
        self.repeat_x = repeat_x
        self.repeat_y = repeat_y
        self.z_index = z_index

        # Tiled texture mode (simple)
        self.tile_texture: Optional[pygame.Surface] = None
        self.tile_offset: pygame.Vector2 = pygame.Vector2(0, 0)

        # Sprite collection mode (advanced)
        self.sprites: List[ParallaxSprite] = []

        # Internal state
        self.origin_offset: pygame.Vector2 = pygame.Vector2(0, 0)  # accumulated scroll

    def set_tiled_texture(self, texture: pygame.Surface):
        """Switch this layer to tiled rendering using a single texture."""
        self.tile_texture = texture
        self.sprites.clear()

    def add_sprite(self, sprite: ParallaxSprite):
        """Add an individual sprite to this layer (automatically disables tiled mode)."""
        self.tile_texture = None
        self.sprites.append(sprite)

    def add_sprites(self, sprites: List[ParallaxSprite]):
        self.tile_texture = None
        self.sprites.extend(sprites)

    def clear_sprites(self):
        self.sprites.clear()

    def populate_random(self,
                        surface: pygame.Surface,
                        count: int,
                        area: pygame.Rect,               # world rectangle to fill
                        scale_range: Tuple[float, float] = (1.0, 1.0),
                        speed_range: Tuple[float, float] = (0.0, 0.0),  # not used per sprite, kept for API
                        oscillate_x_range: Tuple[float, float] = (0.0, 0.0),
                        oscillate_y_range: Tuple[float, float] = (0.0, 0.0),
                        oscillate_speed_range: Tuple[float, float] = (0.5, 2.0),
                        brightness_pulse_range: Tuple[float, float] = (0.0, 0.0),
                        brightness_speed_range: Tuple[float, float] = (0.5, 2.0),
                        alpha_range: Tuple[float, float] = (1.0, 1.0),
                        angle_range: Tuple[float, float] = (0.0, 0.0),
                        seed: Optional[int] = None):
        """
        Fill the layer with randomly placed sprites using the same surface.
        
        Args:
            surface: The image to use for all sprites.
            count: Number of sprites to create.
            area: World rectangle (x, y, width, height) where sprites will be placed.
            scale_range: (min, max) uniform scale.
            oscillate_x_range: (min, max) oscillation amplitude in X (world units).
            oscillate_y_range: (min, max) oscillation amplitude in Y.
            oscillate_speed_range: (min, max) oscillation frequency (Hz).
            brightness_pulse_range: (min, max) brightness pulsation amplitude.
            brightness_speed_range: (min, max) pulsation speed (Hz).
            alpha_range: (min, max) opacity.
            angle_range: (min, max) rotation angle (degrees).
            seed: Optional random seed for reproducibility.
        """
        if seed is not None:
            random.seed(seed)
        self.tile_texture = None
        for _ in range(count):
            # Random position inside area
            px = random.uniform(area.left, area.right)
            py = random.uniform(area.top, area.bottom)
            scale = random.uniform(*scale_range)
            oscillate_x = random.uniform(*oscillate_x_range)
            oscillate_y = random.uniform(*oscillate_y_range)
            osc_speed = random.uniform(*oscillate_speed_range)
            brightness_pulse = random.uniform(*brightness_pulse_range)
            brightness_speed = random.uniform(*brightness_speed_range)
            alpha = random.uniform(*alpha_range)
            angle = random.uniform(*angle_range)
            phase = random.uniform(0, 2*math.pi)

            sprite = ParallaxSprite(
                surface=surface,
                base_pos=pygame.Vector2(px, py),
                scale=scale,
                alpha=alpha,
                angle=angle,
                oscillate_x=oscillate_x,
                oscillate_y=oscillate_y,
                oscillate_speed=osc_speed,
                phase_offset=phase,
                brightness_pulse=brightness_pulse,
                brightness_speed=brightness_speed
            )
            self.sprites.append(sprite)


class ParallaxBackground:
    """
    Manager for multiple parallax layers.
    Provides global time for animations and brightness pulsations.
    """
    def __init__(self, camera: 'Camera'):
        self.camera = camera
        self.layers: List[ParallaxLayer] = []
        self.enabled = True
        self._time: float = 0.0          # global animation clock (seconds)
        self._last_cam_pos: pygame.Vector2 = pygame.Vector2(0, 0)

    def add_layer(self, speed: Tuple[float, float] = (1.0, 1.0),
                  repeat_x: bool = True, repeat_y: bool = True,
                  z_index: int = 0) -> ParallaxLayer:
        """Create and return a new empty layer."""
        layer = ParallaxLayer(speed, repeat_x, repeat_y, z_index)
        self.layers.append(layer)
        self.layers.sort(key=lambda l: l.z_index)
        return layer

    def remove_layer(self, layer: ParallaxLayer):
        if layer in self.layers:
            self.layers.remove(layer)

    def clear(self):
        self.layers.clear()

    def update(self, dt: float):
        """
        Update global animation time and layer scroll offsets.
        Call this once per frame from Camera.update().
        """
        if not self.enabled:
            return
        self._time += dt

        # Update each layer's scroll offset based on camera movement
        cam_pos = self.camera._position   # world centre
        delta = cam_pos - self._last_cam_pos
        self._last_cam_pos = cam_pos

        for layer in self.layers:
            # The origin offset moves opposite to camera, scaled by (1 - speed)
            move = pygame.Vector2(
                delta.x * (1.0 - layer.speed.x),
                delta.y * (1.0 - layer.speed.y)
            )
            layer.origin_offset -= move

            # If using tiled texture, keep offset within texture size to avoid drift
            if layer.tile_texture:
                tex_w, tex_h = layer.tile_texture.get_size()
                if tex_w > 0 and layer.repeat_x:
                    layer.origin_offset.x %= tex_w
                if tex_h > 0 and layer.repeat_y:
                    layer.origin_offset.y %= tex_h

    def render(self, renderer: OpenGLRenderer, viewport: Optional[pygame.Rect] = None):
        """
        Render all layers onto the screen.
        Each layer either renders a tiled texture or a list of animated sprites.
        """
        if not self.enabled:
            return
        if viewport is None:
            viewport = pygame.Rect(0, 0, renderer.width, renderer.height)

        for layer in self.layers:
            if layer.tile_texture:
                self._render_tiled(renderer, layer, viewport)
            else:
                self._render_sprites(renderer, layer, viewport)

    def _render_tiled(self, renderer: OpenGLRenderer, layer: ParallaxLayer, viewport: pygame.Rect):
        """Efficient tiled rendering (same as before)."""
        tex = layer.tile_texture
        if not tex:
            return
        tex_w, tex_h = tex.get_size()
        if tex_w == 0 or tex_h == 0:
            return

        offset = layer.origin_offset
        # First tile origin in screen space
        start_x = int(offset.x) % tex_w
        start_y = int(offset.y) % tex_h

        # Draw tiles covering the viewport
        for y in range(start_y - tex_h, viewport.height + tex_h, tex_h):
            for x in range(start_x - tex_w, viewport.width + tex_w, tex_w):
                tile_rect = pygame.Rect(x, y, tex_w, tex_h)
                if tile_rect.colliderect(viewport):
                    renderer.blit(tex, (x, y))

    def _render_sprites(self, renderer: OpenGLRenderer, layer: ParallaxLayer, viewport: pygame.Rect):
        """Render individual sprites with animation and brightness."""
        camera = self.camera
        zoom = camera.zoom
        time = self._time

        for sprite in layer.sprites:
            # Animated offset (oscillation)
            anim_offset = sprite.get_animated_offset(time)
            
            # Effective world position = base_pos + layer scroll offset + animation offset
            world_pos = sprite.base_pos + layer.origin_offset + anim_offset

            # Convert to screen coordinates (pixels)
            screen_pos = camera.world_to_screen(world_pos)

            # Compute scaled size (original size * scale * zoom)
            orig_w, orig_h = sprite.surface.get_size()
            final_w = int(orig_w * sprite.scale * zoom)
            final_h = int(orig_h * sprite.scale * zoom)
            if final_w <= 0 or final_h <= 0:
                continue
            
            # Compute final color (brightness pulse + fixed tint)
            pulse = sprite.get_current_brightness(time)
            r = min(1.0, sprite.color[0] * pulse)
            g = min(1.0, sprite.color[1] * pulse)
            b = min(1.0, sprite.color[2] * pulse)

            # Prepare a scaled & rotated surface (caching recommended for production)
            coloured_surf = sprite.get_transformed_surface(
                (final_w, final_h),
                sprite.angle,
                (r, g, b, sprite.alpha)
            )
            renderer.blit(coloured_surf, (screen_pos.x - final_w//2, screen_pos.y - final_h//2))   

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
            return (size[0] * self.zoom, size[1] * self.zoom)
        elif isinstance(size, (int, float, np.float32)):
            return size * self.zoom
        elif isinstance(size, pygame.Vector2):
            return size * self.zoom
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

    def get_transform_matrix(self):
        # Assuming zoom factors sx, sy and translation tx, ty (screen offset)
        return np.array([[self.zoom_x, 0, self.tx],
                        [0, self.zoom_y, self.ty]], dtype=np.float32)
        
    def get_view_projection_matrix(self,
                               width: Optional[int] = None,
                               height: Optional[int] = None,
                               column_major: bool = False) -> np.ndarray:
        """
        Return a 4x4 view-projection matrix that maps world coordinates to clip space
        (normalized device coordinates, range [-1, 1] on both axes, Y up).

        The matrix is constructed as: clip = S * R * T
        where:
            T = translation by -camera position
            R = rotation by -camera.rotation (around the camera center)
            S = scale by (2 * zoom / viewport_width, 2 * zoom / viewport_height)

        Args:
            width:  Viewport width in pixels. If None, uses self.viewport_width.
            height: Viewport height in pixels. If None, uses self.viewport_height.
            column_major: If True, return the matrix in column‑major order (for OpenGL).
                        Otherwise, return row‑major.

        Returns:
            A 4x4 numpy array of float32.
        """
        w = self.viewport_width if width is None else width
        h = self.viewport_height if height is None else height
        zoom = self.zoom
        pos = self._position

        # Rotation angle (in radians) – negative to align with world_to_screen convention
        angle = -math.radians(self.rotation)

        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # Scale factors
        sx = 2.0 * zoom / w
        sy = 2.0 * zoom / h

        # Upper 2x2 = S * R
        m00 = sx * cos_a
        m01 = -sx * sin_a
        m10 = sy * sin_a
        m11 = sy * cos_a

        # Translation part = - (S * R) * pos
        tx = -(m00 * pos.x + m01 * pos.y)
        ty = -(m10 * pos.x + m11 * pos.y)

        # Build 4x4 matrix (row‑major)
        matrix = np.array([
            [m00, m01, 0.0, tx],
            [m10, m11, 0.0, ty],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0]
        ], dtype=np.float32)

        if column_major:
            # OpenGL expects column‑major, so transpose
            matrix = matrix.T

        return matrix

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
        self.parallax.clear()

    def render_parallax(self, renderer) -> None:
        """Render the parallax background."""
        self.parallax.render(renderer)

    def enable_parallax(self, enabled: bool = True):
        """Enable/disable parallax rendering."""
        self.parallax.enabled = enabled

    def get_parallax_layer_count(self) -> int:
        """Number of active parallax layers."""
        return len(self.parallax.layers)
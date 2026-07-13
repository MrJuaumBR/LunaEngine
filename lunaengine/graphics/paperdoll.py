"""
Paperdoll System - Modular character rendering with layered sprites.

Allows combining multiple layers (head, body, feet) from a single spritesheet
into a unified character, with independent animations per layer.
Supports scaling and resizing at draw time.
"""

import json
import io
import pygame
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple, Any

from ..backend.types import Color
from ..storage import Atlas, AtlasItem


# ============================================================================
# Layer class
# ============================================================================
class Layer:
    """
    Represents one visual layer of the paperdoll (e.g., head, body, feet).

    Attributes:
        id (str): Unique identifier (e.g., "head").
        src_y (int): Vertical offset in the spritesheet frame (in pixels).
        height (int): Height of this layer (typically frame_height / number_of_layers).
        width (int): Width of this layer (same as frame_width).
        offset_x, offset_y (int): Extra pixel offset when drawing (for fine tuning).
        opacity (float): 0.0 to 1.0 (currently not used in rendering, but kept for future).
        visible (bool): Whether to draw this layer.
        texture_override (pygame.Surface | None): If set, use this surface instead of the main texture.
    """
    def __init__(self, layer_id: str, src_y: int, height: int,
                 width: int = 32, offset_x: int = 0, offset_y: int = 0,
                 opacity: float = 1.0, visible: bool = True):
        self.id = layer_id
        self.src_y = src_y
        self.height = height
        self.width = width
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.opacity = opacity
        self.visible = visible
        self.texture_override: Optional[pygame.Surface] = None

    def set_texture(self, surface: pygame.Surface) -> None:
        """Override the texture for this layer (e.g., equipment)."""
        self.texture_override = surface

    def reset_texture(self) -> None:
        """Revert to using the main spritesheet texture."""
        self.texture_override = None


# ============================================================================
# Animation class
# ============================================================================
class Animation:
    """
    Simple frame‑based animation.

    Attributes:
        name (str): Animation name (e.g., "walk").
        frames (List[int]): List of frame indices (0‑based) to play.
        duration (int): Duration per frame in milliseconds.
    """
    def __init__(self, name: str, frames: List[int], duration: int, loop:Optional[bool]=False):
        self.name = name
        self.frames = frames
        self.duration = duration  # milliseconds per frame
        self.loop = loop

    def get_frame(self, progress: int) -> int:
        """Return the frame index for the given progress (auto‑loops)."""
        if not self.frames:
            return 0
        return self.frames[progress % len(self.frames)]

    @property
    def total_frames(self) -> int:
        return len(self.frames)


# ============================================================================
# Paperdoll class (main)
# ============================================================================
class Paperdoll:
    """
    A modular character made of stacked layers from a single spritesheet.

    Attributes:
        texture (pygame.Surface): The main spritesheet surface.
        frame_w (int): Width of each animation frame.
        frame_h (int): Height of each animation frame.
        pivot_x, pivot_y (int): Anchor point (relative to the frame) used for positioning.
        scale (float): Render scale factor (1.0 = original size).
        layers (Dict[str, Layer]): All layers, keyed by id.
        layer_order (List[str]): Order in which layers are drawn (bottom → top).
        animations (Dict[str, Animation]): All animations, keyed by name.
        current_anim (str): Currently playing animation name.
        current_frame (int): Current frame progress index (not the sprite index).
        timer (float): Accumulated time in seconds.
        speed (float): Playback speed multiplier (1.0 = normal).
    """
    def __init__(self, texture: pygame.Surface, frame_w: int, frame_h: int,
                 pivot_x: int = 0, pivot_y: int = 0):
        self.texture = texture
        self.frame_w = frame_w
        self.frame_h = frame_h
        self.pivot_x = pivot_x
        self.pivot_y = pivot_y
        self.scale = 1.0

        self.layers: Dict[str, Layer] = {}
        self.layer_order: List[str] = []
        self.animations: Dict[str, Animation] = {}

        self.current_anim: str = ""
        self.current_frame: int = 0
        self.timer: float = 0.0
        self.speed: float = 1.0

    # --- Layer management ---
    def add_layer(self, layer: Layer) -> None:
        """Add a layer (appended to the end of the draw order)."""
        self.layers[layer.id] = layer
        self.layer_order.append(layer.id)

    def get_layer(self, layer_id: str) -> Optional[Layer]:
        """Retrieve a layer by its id."""
        return self.layers.get(layer_id)

    def set_layer_texture(self, layer_id: str, surface: pygame.Surface) -> None:
        """Replace the texture of a specific layer (e.g., helmet)."""
        layer = self.get_layer(layer_id)
        if layer:
            layer.set_texture(surface)

    def set_layer_visible(self, layer_id: str, visible: bool) -> None:
        """Show or hide a layer."""
        layer = self.get_layer(layer_id)
        if layer:
            layer.visible = visible

    # --- Animation management ---
    def add_animation(self, anim: Animation) -> None:
        """Register an animation."""
        self.animations[anim.name] = anim

    def play(self, anim_name: str, reset: bool = True) -> None:
        """
        Start playing an animation.

        Args:
            anim_name: Name of the animation (must exist).
            reset: If True, reset frame progress to 0.
        """
        if anim_name not in self.animations:
            raise KeyError(f"Animation '{anim_name}' not found.")
        if self.current_anim != anim_name or reset:
            self.current_anim = anim_name
            self.current_frame = 0
            self.timer = 0.0

    # --- Scaling and resizing ---
    def set_scale(self, scale: float) -> None:
        """
        Set the render scale factor.

        Args:
            scale: Multiplier (1.0 = original size). Must be > 0.
        """
        if scale <= 0:
            raise ValueError("Scale must be > 0")
        self.scale = scale

    def set_size(self, width: int, height: int, keep_aspect: bool = True) -> None:
        """
        Resize the rendered character to the given dimensions.

        This calculates the scale factor needed to fit the character into the
        specified box. If keep_aspect is True, the scale is chosen to fit
        entirely inside the box while preserving the original aspect ratio.
        Otherwise, the scale is calculated independently for width and height
        (stretching/squashing).

        Args:
            width: Desired width in pixels.
            height: Desired height in pixels.
            keep_aspect: If True, preserve the original aspect ratio.
        """
        if width <= 0 or height <= 0:
            raise ValueError("Width and height must be > 0")

        orig_w = self.frame_w
        orig_h = self.frame_h

        if keep_aspect:
            scale_x = width / orig_w
            scale_y = height / orig_h
            self.scale = min(scale_x, scale_y)
        else:
            print("Warning: set_size with keep_aspect=False is not fully supported yet; using width scale and preserving aspect.")
            self.scale = width / orig_w

    # --- Update loop ---
    def update(self, dt: float) -> None:
        """Advance the animation timer and update the current frame."""
        if not self.current_anim:
            return

        anim = self.animations[self.current_anim]
        frame_time = (anim.duration / 1000.0) / (self.speed if self.speed != 0 else 1.0)

        self.timer += dt
        if self.timer >= frame_time:
            self.timer = 0.0
            self.current_frame += 1
            # For non‑looping animations, freeze on the last frame.
            if anim.loop:
                if self.current_frame >= anim.total_frames:
                    self.current_frame = 0
            elif self.current_frame >= anim.total_frames and not anim.loop:
                self.current_frame = anim.total_frames - 1

    # --- Rendering ---
    def draw(self, renderer, x: int, y: int) -> None:
        """
        Draw the paperdoll at the given screen position with current scale.

        Args:
            renderer: An instance of OpenGLRenderer (or any renderer with blit()).
            x, y: Screen coordinates (before pivot adjustment).
        """
        if not self.current_anim:
            return

        anim = self.animations[self.current_anim]
        frame_index = anim.get_frame(self.current_frame)
        src_x = frame_index * self.frame_w

        # Apply pivot and scale
        draw_x = x - self.pivot_x * self.scale
        draw_y = y - self.pivot_y * self.scale

        # Draw layers in order (bottom → top)
        for layer_id in self.layer_order:
            layer = self.layers.get(layer_id)
            if not layer or not layer.visible:
                continue

            # Choose texture: override or main
            tex = layer.texture_override if layer.texture_override else self.texture

            # Original source rectangle (within the texture)
            src_rect = pygame.Rect(src_x, layer.src_y, self.frame_w, layer.height)

            # Destination rectangle with scaled size
            dest_w = int(self.frame_w * self.scale)
            dest_h = int(layer.height * self.scale)
            dest_x = draw_x + layer.offset_x * self.scale
            dest_y = draw_y + layer.offset_y * self.scale
            dest_rect = pygame.Rect(dest_x, dest_y, dest_w, dest_h)

            # Blit with scaling (pass dest as Rect so renderer uses its size)
            renderer.blit(tex, dest_rect, area=src_rect, pivot=(0.0, 0.0))
    

# ============================================================================
# Loader functions
# ============================================================================
def load_paperdoll(config_path: Union[str, Path, AtlasItem]) -> Paperdoll:
    """
    Load a paperdoll from a JSON configuration file and its associated spritesheet.

    The JSON must contain:
        - "texture": path to the spritesheet image.
        - "frame_width", "frame_height": dimensions of each frame.
        - "pivot": {"x", "y"} (optional, defaults to 0,0).
        - "layers": list of {"id", "src_y", "height", "offset_x", "offset_y", "opacity", "visible"}.
        - "animations": dict with animation names, each containing "frames" (list of ints) and "duration" (ms).
        - "default_animation": (optional) name of the animation to start with.
    """
    if isinstance(config_path, AtlasItem):
        config_path = config_path.path
    elif isinstance(config_path, str):
        config_path = Path(config_path)
    elif not isinstance(config_path, Path):
        raise TypeError("config_path must be a string, Path, or AtlasItem.")

    if not config_path.exists():
        raise FileNotFoundError(f"Paperdoll config file not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Load the texture (using pygame, as the engine does)
    tex_path = Path(data['texture'])
    if not tex_path.is_absolute():
        tex_path = config_path.parent / tex_path
    texture = pygame.image.load(str(tex_path)).convert_alpha()

    frame_w = data['frame_width']
    frame_h = data['frame_height']
    pivot = data.get('pivot', {})
    pivot_x = pivot.get('x', 0)
    pivot_y = pivot.get('y', 0)

    paperdoll = Paperdoll(texture, frame_w, frame_h, pivot_x, pivot_y)

    # Load layers
    for layer_data in data.get('layers', []):
        layer = Layer(
            layer_id=layer_data['id'],
            src_y=layer_data['src_y'],
            height=layer_data['height'],
            width=frame_w,
            offset_x=layer_data.get('offset', {}).get('x', 0),
            offset_y=layer_data.get('offset', {}).get('y', 0),
            opacity=layer_data.get('opacity', 1.0),
            visible=layer_data.get('visible', True)
        )
        paperdoll.add_layer(layer)

    # Load animations
    for anim_name, anim_data in data.get('animations', {}).items():
        anim = Animation(
            name=anim_name,
            frames=anim_data['frames'],
            duration=anim_data['duration'],
            loop=anim_data.get('loop', False)
        )
        paperdoll.add_animation(anim)

    # Start default animation
    default = data.get('default_animation', 'idle')
    if default in paperdoll.animations:
        paperdoll.play(default)

    return paperdoll


def load_paperdoll_from_atlas(config_name: str, atlas: Atlas) -> Paperdoll:
    """
    Load a paperdoll from an Atlas entry that contains a JSON configuration.

    The atlas item with the given name must be a JSON file.
    The JSON must reference the spritesheet texture (the path can be relative to the config).
    If the texture is also stored in the atlas, you can use the atlas to load it.
    """
    # Get the config bytes from the atlas
    config_bytes = atlas.get_bytes(config_name)
    if config_bytes is None:
        raise FileNotFoundError(f"Atlas item '{config_name}' not found or not loaded.")

    # Load JSON from bytes
    data = json.loads(config_bytes.decode('utf-8'))

    # Load the texture: first try to get it from the atlas, else fallback to file
    tex_name = data.get('texture')
    if tex_name is None:
        raise ValueError("JSON missing 'texture' field.")

    tex_bytes = atlas.get_bytes(tex_name)
    if tex_bytes is not None:
        texture = pygame.image.load(io.BytesIO(tex_bytes)).convert_alpha()
    else:
        # Fallback: load from file system (relative to the config path)
        # Since we don't have a file path, we assume the texture is in the atlas.
        raise FileNotFoundError(f"Texture '{tex_name}' not found in atlas.")

    frame_w = data['frame_width']
    frame_h = data['frame_height']
    pivot = data.get('pivot', {})
    pivot_x = pivot.get('x', 0)
    pivot_y = pivot.get('y', 0)

    paperdoll = Paperdoll(texture, frame_w, frame_h, pivot_x, pivot_y)

    # Layers
    for layer_data in data.get('layers', []):
        layer = Layer(
            layer_id=layer_data['id'],
            src_y=layer_data['src_y'],
            height=layer_data['height'],
            width=frame_w,
            offset_x=layer_data.get('offset', {}).get('x', 0),
            offset_y=layer_data.get('offset', {}).get('y', 0),
            opacity=layer_data.get('opacity', 1.0),
            visible=layer_data.get('visible', True)
        )
        paperdoll.add_layer(layer)

    # Animations
    for anim_name, anim_data in data.get('animations', {}).items():
        anim = Animation(
            name=anim_name,
            frames=anim_data['frames'],
            duration=anim_data['duration'],
            loop=anim_data.get('loop', False)
        )
        paperdoll.add_animation(anim)

    default = data.get('default_animation', 'idle')
    if default in paperdoll.animations:
        paperdoll.play(default)

    return paperdoll
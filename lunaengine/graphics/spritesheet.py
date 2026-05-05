"""
Sprite Sheet System with Alpha Support and Time-Based Animations

LOCATION: lunaengine/graphics/spritesheet.py

DESCRIPTION:
Advanced sprite sheet management system with alpha channel support and
time-based animation system. Provides efficient sprite extraction from
texture atlases with flexible positioning and frame-rate independent animations.

KEY FEATURES:
- Full alpha channel support for transparent sprites
- Flexible sprite extraction using Rect coordinates
- Batch sprite extraction for multiple regions
- Time-based animation system (frame-rate independent)
- Support for padding, margin, and scaling
- Animation sequencing with configurable durations
- Automatic frame extraction based on parameters
- Image manipulation: scaling, resizing, masking, color replacement, tinting

LIBRARIES USED:
- pygame: Image loading, surface manipulation, and alpha processing
- typing: Type hints for better code documentation
- time: Animation timing calculations
- pathlib: Modern path handling

! WARN:
- Ensure pygame is initialized before using this module

USAGE:
>>> # Basic sprite sheet
>>> spritesheet = SpriteSheet("characters.png")
>>> single_sprite = spritesheet.get_sprite_at_rect(pygame.Rect(0, 0, 64, 64))
>>>
>>> # Multiple sprites
>>> regions = [pygame.Rect(0, 0, 64, 64), pygame.Rect(64, 0, 64, 64)]
>>> sprites = spritesheet.get_sprites_at_regions(regions)
>>>
>>> # Animation - automatically extracts frames
>>> walk_animation = Animation("tiki_texture.png", (70, 70), (0, 0), frame_count=6,
>>>                           scale=(2, 2), duration=1.0)
>>> current_frame = walk_animation.get_current_frame()
>>>
>>> # Color replacement
>>> recolored = SpriteSheet.replace_color(sprite, (255,0,0), (0,255,0), tolerance=10)
>>>
>>> # Tinting
>>> tinted = SpriteSheet.tint(sprite, (100,100,255))
"""

import pygame
import time
from pathlib import Path
from typing import List, Tuple, Optional, Union, Callable


class SpriteSheet:
    """
    Main sprite sheet class for managing and extracting sprites from texture atlases.

    This class handles loading sprite sheets with alpha support and provides
    multiple methods for extracting individual sprites or sprite sequences,
    as well as various image manipulation utilities.

    Attributes:
        sheet (pygame.Surface): The loaded sprite sheet surface with alpha
        filepath (Path): Path to the sprite sheet file
        width (int): Width of the sprite sheet
        height (int): Height of the sprite sheet
    """

    def __init__(self, filename: Union[str, Path]):
        """
        Initialize the sprite sheet with alpha support.

        Args:
            filename (Union[str, Path]): Path to the sprite sheet image file

        Raises:
            FileNotFoundError: If the file does not exist
        """
        self.filepath = Path(filename).resolve()
        if not self.filepath.exists():
            raise FileNotFoundError(f"Sprite sheet file not found: {self.filepath}")

        self.sheet = pygame.image.load(str(self.filepath)).convert_alpha()
        self.width = self.sheet.get_width()
        self.height = self.sheet.get_height()

    def get_sprite_at_rect(self, rect: Union[pygame.Rect, Tuple[int, int, int, int]]) -> pygame.Surface:
        """
        Extract a sprite from a specific rectangular region.

        Args:
            rect (Union[pygame.Rect, Tuple[int, int, int, int]]): Rectangle defining the sprite region
                (x, y, width, height)

        Returns:
            pygame.Surface: The extracted sprite surface with alpha

        Raises:
            ValueError: If the rect is outside the sprite sheet bounds
        """
        # Accepts tuples on rect
        if isinstance(rect, tuple) and len(rect) == 4:
            rect = pygame.Rect(*rect)

        # Validate rect bounds
        if (
            rect.x < 0
            or rect.y < 0
            or rect.x + rect.width > self.width
            or rect.y + rect.height > self.height
        ):
            raise ValueError(
                f"Rect {rect} is outside sprite sheet bounds {self.width}x{self.height}"
            )

        # Extract the sprite using subsurface (no memory copy)
        return self.sheet.subsurface(rect)

    def get_sprites_at_regions(
        self, regions: List[Union[pygame.Rect, Tuple[int, int, int, int]]]
    ) -> List[pygame.Surface]:
        """
        Extract multiple sprites from a list of rectangular regions.

        Args:
            regions (List[Union[pygame.Rect, Tuple[int, int, int, int]]]): List of rectangles defining sprite regions

        Returns:
            List[pygame.Surface]: List of extracted sprite surfaces
        """
        sprites = []
        for rect in regions:
            try:
                sprite = self.get_sprite_at_rect(rect)
                sprites.append(sprite)
            except ValueError as e:
                print(f"Warning: Skipping invalid region {rect}: {e}")

        return sprites

    def get_sprite_grid(
        self, cell_size: Tuple[int, int], grid_pos: Tuple[int, int]
    ) -> pygame.Surface:
        """
        Extract a sprite from a grid-based sprite sheet.

        Args:
            cell_size (Tuple[int, int]): Width and height of each grid cell
            grid_pos (Tuple[int, int]): Grid coordinates (col, row)

        Returns:
            pygame.Surface: The extracted sprite surface
        """
        cell_width, cell_height = cell_size
        col, row = grid_pos

        rect = pygame.Rect(col * cell_width, row * cell_height, cell_width, cell_height)

        return self.get_sprite_at_rect(rect)

    def get_surface_drawn_area(
        self, surface: pygame.Surface, threshold: int = 1
    ) -> pygame.Rect:
        """
        Get the bounding rectangle of the non-transparent (drawn) area of a surface.

        This function analyzes the alpha channel of the surface to find the smallest
        rectangle that contains all non-transparent pixels, creating a tight hitbox.

        Args:
            surface (pygame.Surface): Surface to analyze (must have alpha channel)
            threshold (int): Alpha threshold value (0-255). Pixels with alpha >= threshold
                            are considered drawn. Default is 1 (any non-fully-transparent).

        Returns:
            pygame.Rect: Tight bounding rectangle around the non-transparent area.
                        Returns empty Rect (0,0,0,0) if surface is fully transparent.

        Raises:
            ValueError: If surface doesn't have per-pixel alpha
        """
        if not (surface.get_flags() & pygame.SRCALPHA):
            raise ValueError(
                "Surface must have per-pixel alpha for drawn area detection"
            )

        width, height = surface.get_size()
        if width == 0 or height == 0:
            return pygame.Rect(0, 0, 0, 0)

        # Lock surface for pixel access
        surface.lock()
        try:
            # Initialize bounds to extreme values
            left, top = width, height
            right, bottom = -1, -1

            # Iterate through all pixels to find non-transparent bounds
            for y in range(height):
                for x in range(width):
                    # Get alpha value at current pixel
                    alpha = surface.get_at((x, y))[3]  # Index 3 is alpha channel
                    # Check if pixel is non-transparent (above threshold)
                    if alpha >= threshold:
                        if x < left:
                            left = x
                        if x > right:
                            right = x
                        if y < top:
                            top = y
                        if y > bottom:
                            bottom = y

            # Check if any non-transparent pixels were found
            if left <= right and top <= bottom:
                return pygame.Rect(left, top, right - left + 1, bottom - top + 1)
            else:
                return pygame.Rect(0, 0, 0, 0)  # Fully transparent surface
        finally:
            # Always unlock the surface
            surface.unlock()

    # --------------------------------------------------------------------------
    # Image manipulation utilities (static methods)
    # --------------------------------------------------------------------------

    @staticmethod
    def scale_surface(
        surface: pygame.Surface,
        scale_x: float,
        scale_y: float,
        smooth: bool = True
    ) -> pygame.Surface:
        """
        Scale a surface by the given factors.

        Args:
            surface (pygame.Surface): Surface to scale
            scale_x (float): Horizontal scale factor (>0)
            scale_y (float): Vertical scale factor (>0)
            smooth (bool): If True, use smooth scaling (SmoothScale)

        Returns:
            pygame.Surface: The scaled surface
        """
        new_width = max(1, int(surface.get_width() * scale_x))
        new_height = max(1, int(surface.get_height() * scale_y))

        if smooth:
            return pygame.transform.smoothscale(surface, (new_width, new_height))
        else:
            return pygame.transform.scale(surface, (new_width, new_height))

    @staticmethod
    def resize_surface(
        surface: pygame.Surface,
        new_width: int,
        new_height: int,
        smooth: bool = True
    ) -> pygame.Surface:
        """
        Resize a surface to exact dimensions.

        Args:
            surface (pygame.Surface): Surface to resize
            new_width (int): Target width in pixels
            new_height (int): Target height in pixels
            smooth (bool): If True, use smooth scaling

        Returns:
            pygame.Surface: The resized surface
        """
        new_width = max(1, new_width)
        new_height = max(1, new_height)

        if smooth:
            return pygame.transform.smoothscale(surface, (new_width, new_height))
        else:
            return pygame.transform.scale(surface, (new_width, new_height))

    @staticmethod
    def create_mask(
        surface: pygame.Surface,
        color_key: Optional[Tuple[int, int, int]] = None,
        threshold: int = 0
    ) -> pygame.Mask:
        """
        Create a collision mask from a surface.

        Args:
            surface (pygame.Surface): Surface to create mask from
            color_key (Optional[Tuple[int, int, int]]): If provided, treat this RGB color as transparent.
                Otherwise use alpha channel.
            threshold (int): Alpha threshold for non-transparent pixels (0-255). Ignored if color_key is used.

        Returns:
            pygame.Mask: The generated mask
        """
        if color_key is not None:
            # Create a copy and set colorkey
            temp_surface = surface.copy()
            temp_surface.set_colorkey(color_key)
            return pygame.mask.from_surface(temp_surface)
        else:
            # Use alpha channel
            return pygame.mask.from_surface(surface, threshold)

    @staticmethod
    def replace_color(
        surface: pygame.Surface,
        old_color: Union[Tuple[int, int, int], Tuple[int, int, int, int]],
        new_color: Union[Tuple[int, int, int], Tuple[int, int, int, int]],
        tolerance: int = 0
    ) -> pygame.Surface:
        """
        Replace a specific color (or color range) in a surface with another color.

        Args:
            surface (pygame.Surface): Source surface
            old_color (Union[Tuple[int, int, int], Tuple[int, int, int, int]]): RGB or RGBA color to replace
            new_color (Union[Tuple[int, int, int], Tuple[int, int, int, int]]): RGB or RGBA replacement color
            tolerance (int): Color matching tolerance (0-255). Higher values replace similar colors.

        Returns:
            pygame.Surface: A new surface with colors replaced
        """
        # Normalize colors to RGBA
        old_rgba = old_color if len(old_color) == 4 else (*old_color, 255)
        new_rgba = new_color if len(new_color) == 4 else (*new_color, 255)

        # Create a copy of the surface
        result = surface.copy()
        width, height = result.get_size()

        # Lock surfaces for pixel access
        result.lock()
        try:
            for y in range(height):
                for x in range(width):
                    pixel = result.get_at((x, y))
                    # Check if pixel matches old_color within tolerance
                    if tolerance == 0:
                        if pixel[:3] == old_rgba[:3] and pixel[3] == old_rgba[3]:
                            result.set_at((x, y), new_rgba)
                    else:
                        # Calculate color distance
                        dr = abs(pixel[0] - old_rgba[0])
                        dg = abs(pixel[1] - old_rgba[1])
                        db = abs(pixel[2] - old_rgba[2])
                        da = abs(pixel[3] - old_rgba[3])
                        if dr <= tolerance and dg <= tolerance and db <= tolerance and da <= tolerance:
                            result.set_at((x, y), new_rgba)
        finally:
            result.unlock()

        return result

    @staticmethod
    def replace_color_range(
        surface: pygame.Surface,
        color_low: Tuple[int, int, int],
        color_high: Tuple[int, int, int],
        new_color: Union[Tuple[int, int, int], Tuple[int, int, int, int]],
        alpha_tolerance: int = 0
    ) -> pygame.Surface:
        """
        Replace all colors within a bounding box in RGB space.

        Args:
            surface (pygame.Surface): Source surface
            color_low (Tuple[int, int, int]): Minimum RGB values (inclusive)
            color_high (Tuple[int, int, int]): Maximum RGB values (inclusive)
            new_color (Union[Tuple[int, int, int], Tuple[int, int, int, int]]): Replacement RGB or RGBA
            alpha_tolerance (int): Alpha channel tolerance (0-255)

        Returns:
            pygame.Surface: A new surface with colors replaced
        """
        new_rgba = new_color if len(new_color) == 4 else (*new_color, 255)
        result = surface.copy()
        width, height = result.get_size()

        result.lock()
        try:
            for y in range(height):
                for x in range(width):
                    pixel = result.get_at((x, y))
                    if (color_low[0] <= pixel[0] <= color_high[0] and
                        color_low[1] <= pixel[1] <= color_high[1] and
                        color_low[2] <= pixel[2] <= color_high[2] and
                        abs(pixel[3] - new_rgba[3]) <= alpha_tolerance):
                        result.set_at((x, y), new_rgba)
        finally:
            result.unlock()

        return result

    @staticmethod
    def tint(
        surface: pygame.Surface,
        tint_color: Tuple[int, int, int],
        intensity: float = 1.0,
        blend_mode: str = "multiply"
    ) -> pygame.Surface:
        """
        Apply a color tint to a surface.

        Args:
            surface (pygame.Surface): Source surface
            tint_color (Tuple[int, int, int]): RGB tint color
            intensity (float): Tint intensity (0.0 = original, 1.0 = full tint)
            blend_mode (str): Blend mode - "multiply", "add", or "overlay"

        Returns:
            pygame.Surface: Tinted surface

        Raises:
            ValueError: If blend_mode is not supported
        """
        result = surface.copy()
        tint_surface = pygame.Surface(result.get_size(), pygame.SRCALPHA)

        # Apply intensity to tint color
        r, g, b = tint_color
        r = int(r * intensity)
        g = int(g * intensity)
        b = int(b * intensity)

        if blend_mode == "multiply":
            tint_surface.fill((r, g, b, 0))
            result.blit(tint_surface, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        elif blend_mode == "add":
            tint_surface.fill((r, g, b, 0))
            result.blit(tint_surface, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        elif blend_mode == "overlay":
            # Simple overlay: blend with white/black based on original brightness
            for y in range(result.get_height()):
                for x in range(result.get_width()):
                    pixel = result.get_at((x, y))
                    if pixel[3] > 0:
                        # Brightness factor (0-1)
                        brightness = (pixel[0] + pixel[1] + pixel[2]) / (3 * 255)
                        overlay_r = int(pixel[0] * (1 - intensity) + r * intensity * brightness)
                        overlay_g = int(pixel[1] * (1 - intensity) + g * intensity * brightness)
                        overlay_b = int(pixel[2] * (1 - intensity) + b * intensity * brightness)
                        result.set_at((x, y), (overlay_r, overlay_g, overlay_b, pixel[3]))
        else:
            raise ValueError(f"Unsupported blend_mode: {blend_mode}. Use 'multiply', 'add', or 'overlay'.")

        return result

    @staticmethod
    def paint(
        surface: pygame.Surface,
        color: Union[Tuple[int, int, int], Tuple[int, int, int, int]],
        preserve_alpha: bool = True
    ) -> pygame.Surface:
        """
        Paint the entire surface (or all non-transparent pixels) with a solid color.

        Args:
            surface (pygame.Surface): Source surface
            color (Union[Tuple[int, int, int], Tuple[int, int, int, int]]): RGB or RGBA fill color
            preserve_alpha (bool): If True, only paint non-transparent pixels (preserve alpha shape).
                                   If False, fill entire surface including transparent areas.

        Returns:
            pygame.Surface: Painted surface
        """
        fill_color = color if len(color) == 4 else (*color, 255)
        result = surface.copy()

        if preserve_alpha:
            # Only paint pixels that are not fully transparent
            width, height = result.get_size()
            result.lock()
            try:
                for y in range(height):
                    for x in range(width):
                        pixel = result.get_at((x, y))
                        if pixel[3] > 0:
                            result.set_at((x, y), (fill_color[0], fill_color[1], fill_color[2], pixel[3]))
            finally:
                result.unlock()
        else:
            result.fill(fill_color)

        return result

    @staticmethod
    def color_to_alpha(
        surface: pygame.Surface,
        color: Tuple[int, int, int],
        threshold: int = 0
    ) -> pygame.Surface:
        """
        Convert a specific RGB color to transparent (alpha = 0).

        Args:
            surface (pygame.Surface): Source surface
            color (Tuple[int, int, int]): RGB color to make transparent
            threshold (int): Color matching tolerance

        Returns:
            pygame.Surface: Surface with the specified color made transparent
        """
        result = surface.copy()
        width, height = result.get_size()

        result.lock()
        try:
            for y in range(height):
                for x in range(width):
                    pixel = result.get_at((x, y))
                    dr = abs(pixel[0] - color[0])
                    dg = abs(pixel[1] - color[1])
                    db = abs(pixel[2] - color[2])
                    if dr <= threshold and dg <= threshold and db <= threshold:
                        result.set_at((x, y), (pixel[0], pixel[1], pixel[2], 0))
        finally:
            result.unlock()

        return result


class Animation:
    """
    Time-based animation system for sprite sequences with fade effects.

    This class automatically extracts frames from a sprite sheet based on
    the provided parameters and manages animation timing with alpha transitions.

    Attributes:
        spritesheet (SpriteSheet): The source sprite sheet
        frames (List[pygame.Surface]): List of animation frames
        frame_count (int): Total number of frames in the animation
        current_frame_index (int): Current frame index in the animation
        duration (float): Total animation duration in seconds
        frame_duration (float): Duration of each frame in seconds
        last_update_time (float): Last time the animation was updated
        scale (Tuple[float, float]): Scale factors for the animation
        loop (bool): Whether the animation should loop
        playing (bool): Whether the animation is currently playing
        fade_in_duration (float): Duration of fade-in effect in seconds
        fade_out_duration (float): Duration of fade-out effect in seconds
        fade_alpha (int): Current alpha value for fade effects (0-255)
        fade_mode (str): Current fade mode: 'in', 'out', or None
        flip (Tuple[bool, bool]): Flip flags for horizontal and vertical flipping
    """

    def __init__(
        self,
        spritesheet_file: Union[str, Path, SpriteSheet],
        size: Tuple[int, int],
        start_pos: Tuple[int, int] = (0, 0),
        frame_count: int = 1,
        padding: Tuple[int, int] = (0, 0),
        margin: Tuple[int, int] = (0, 0),
        scale: Tuple[float, float] = (1.0, 1.0),
        duration: float = 1.0,
        loop: bool = True,
        fade_in_duration: float = 0.0,
        fade_out_duration: float = 0.0,
        flip: Tuple[bool, bool] = (False, False),
    ):
        """
        Initialize the animation and automatically extract frames from sprite sheet.

        Args:
            spritesheet_file (Union[str, Path, SpriteSheet]): Path to the sprite sheet file or SpriteSheet instance
            size (Tuple[int, int]): Size of each sprite (width, height)
            start_pos (Tuple[int, int]): Starting position in the sprite sheet (x, y)
            frame_count (int): Number of frames to extract for the animation
            padding (Tuple[int, int]): Padding between sprites (x, y)
            margin (Tuple[int, int]): Margin around the sprite sheet (x, y)
            scale (Tuple[float, float]): Scale factors for the animation
            duration (float): Total animation duration in seconds
            loop (bool): Whether the animation should loop
            fade_in_duration (float): Duration of fade-in effect in seconds
            fade_out_duration (float): Duration of fade-out effect in seconds
            flip (Tuple[bool, bool]): Flip the animation horizontally and vertically
        """
        if isinstance(spritesheet_file, (str, Path)):
            self.spritesheet = SpriteSheet(spritesheet_file)
        elif isinstance(spritesheet_file, SpriteSheet):
            self.spritesheet = spritesheet_file
        else:
            raise TypeError("spritesheet_file must be a path string, Path object, or SpriteSheet instance")

        self.size = size
        self.start_pos = start_pos
        self.frame_count = frame_count
        self.padding = padding
        self.margin = margin
        self.scale = scale
        self.duration = duration
        self.loop = loop
        self.playing = True
        self.flip = flip

        # Fade effect properties
        self.fade_in_duration = fade_in_duration
        self.fade_out_duration = fade_out_duration
        self.fade_alpha = 0 if fade_in_duration > 0 else 255
        self.fade_mode = "in" if fade_in_duration > 0 else None
        self.fade_start_time = time.time() if fade_in_duration > 0 else None
        self.fade_progress = 0.0

        # Extract frames automatically based on parameters
        self.frames = self._extract_animation_frames()

        # Animation timing
        self.frame_duration = duration / len(self.frames) if self.frames else 0
        self.current_frame_index = 0
        self.last_update_time = time.time()
        self.accumulated_time = 0.0

        # Apply scaling to frames if needed
        if scale != (1.0, 1.0):
            self._apply_scaling()

    def _extract_animation_frames(self) -> List[pygame.Surface]:
        """
        Automatically extract animation frames based on parameters.

        Creates a sequence of rectangles and extracts the corresponding sprites
        from the sprite sheet.

        Returns:
            List[pygame.Surface]: List of extracted frames
        """
        frames = []
        sprite_width, sprite_height = self.size
        start_x, start_y = self.start_pos
        pad_x, pad_y = self.padding
        margin_x, margin_y = self.margin
        current_x = start_x + margin_x
        current_y = start_y + margin_y

        for i in range(self.frame_count):
            # Create rect for current frame
            rect = pygame.Rect(current_x, current_y, sprite_width, sprite_height)
            try:
                frame = self.spritesheet.get_sprite_at_rect(rect)
                if self.flip[0]:
                    frame = pygame.transform.flip(frame, True, False)
                if self.flip[1]:
                    frame = pygame.transform.flip(frame, False, True)
                frames.append(frame)
            except ValueError as e:
                print(f"Warning: Could not extract frame {i} at {rect}: {e}")
                break

            # Move to next frame position (horizontal layout)
            current_x += sprite_width + pad_x
            # Check if we need to move to next row (if frame goes beyond sheet width)
            if current_x + sprite_width > self.spritesheet.width:
                current_x = margin_x
                current_y += sprite_height + pad_y

        print(f"Animation: Extracted {len(frames)}/{self.frame_count} frames from {self.spritesheet.filepath.name}")

        return frames

    def _apply_scaling(self):
        """Apply scaling to all animation frames."""
        if self.scale == (1.0, 1.0):
            return

        scaled_frames = []
        scale_x, scale_y = self.scale

        for frame in self.frames:
            new_width = int(frame.get_width() * scale_x)
            new_height = int(frame.get_height() * scale_y)
            scaled_frame = pygame.transform.scale(frame, (new_width, new_height))
            scaled_frames.append(scaled_frame)

        self.frames = scaled_frames

    def set_duration(self, new_duration: float):
        """
        Change the animation duration.

        Args:
            new_duration (float): New total duration in seconds
        """
        self.duration = new_duration
        self.frame_duration = new_duration / len(self.frames) if self.frames else 0

    def play(self):
        """Start or resume the animation."""
        self.playing = True
        self.last_update_time = time.time()

    def pause(self):
        """Pause the animation."""
        self.playing = False

    def get_frame_count(self) -> int:
        """
        Get the number of frames in the animation.

        Returns:
            int: Number of frames
        """
        return len(self.frames)

    def get_progress(self) -> float:
        """
        Get the current progress of the animation (0.0 to 1.0).

        Returns:
            float: Animation progress from start (0.0) to end (1.0)
        """
        if len(self.frames) <= 1:
            return 0.0
        return self.current_frame_index / (len(self.frames) - 1)

    def _apply_fade_effect(self, surface: pygame.Surface) -> pygame.Surface:
        """
        Apply current fade alpha to a surface.

        Args:
            surface (pygame.Surface): Original surface

        Returns:
            pygame.Surface: Surface with fade effect applied
        """
        if self.fade_alpha == 255:  # No fade needed
            return surface

        # Create a copy to avoid modifying original frames
        faded_surface = surface.copy()

        # Create a temporary surface for alpha operations
        temp_surface = pygame.Surface(faded_surface.get_size(), pygame.SRCALPHA)
        temp_surface.fill((255, 255, 255, self.fade_alpha))

        # Apply alpha using blend operation
        faded_surface.blit(temp_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        return faded_surface

    def update_fade(self):
        """
        Update fade-in and fade-out effects based on elapsed time.
        """
        current_time = time.time()

        if self.fade_mode == "in":
            if self.fade_start_time is None:
                self.fade_start_time = current_time
                return

            elapsed = current_time - self.fade_start_time
            self.fade_progress = min(elapsed / self.fade_in_duration, 1.0)

            # Calculate alpha from progress (0 to 255)
            self.fade_alpha = int(self.fade_progress * 255)

            # Check if fade-in is complete
            if self.fade_progress >= 1.0:
                self.fade_alpha = 255
                self.fade_mode = None
                self.fade_start_time = None

        elif self.fade_mode == "out":
            if self.fade_start_time is None:
                self.fade_start_time = current_time
                return

            elapsed = current_time - self.fade_start_time
            self.fade_progress = min(elapsed / self.fade_out_duration, 1.0)

            # Calculate alpha from progress (255 to 0)
            self.fade_alpha = int((1.0 - self.fade_progress) * 255)

            # Check if fade-out is complete
            if self.fade_progress >= 1.0:
                self.fade_alpha = 0
                self.fade_mode = None
                self.fade_start_time = None
                self.playing = False

    def update(self):
        """
        Update the animation based on elapsed time including fade effects.

        This method uses time-based animation rather than frame-based,
        making it frame-rate independent.
        """
        # Update fade effects first
        if self.fade_mode:
            self.update_fade()

        if not self.playing or len(self.frames) <= 1:
            return

        current_time = time.time()
        delta_time = current_time - self.last_update_time
        self.last_update_time = current_time

        # Accumulate time and advance frames
        self.accumulated_time += delta_time

        # Calculate how many frames to advance
        frames_to_advance = int(self.accumulated_time / self.frame_duration)

        if frames_to_advance > 0:
            self.accumulated_time -= frames_to_advance * self.frame_duration

            if self.loop:
                self.current_frame_index = (
                    self.current_frame_index + frames_to_advance
                ) % len(self.frames)
            else:
                self.current_frame_index = min(
                    self.current_frame_index + frames_to_advance, len(self.frames) - 1
                )

                # Start fade-out if we reached the end and fade-out is configured
                if (
                    self.current_frame_index >= len(self.frames) - 1
                    and self.fade_out_duration > 0
                    and self.fade_mode is None
                ):
                    self.start_fade_out()

                # Stop animation if we reached the end and not looping
                if (
                    self.current_frame_index >= len(self.frames) - 1
                    and not self.loop
                    and self.fade_out_duration == 0
                ):
                    self.playing = False

    def get_current_frame(self) -> pygame.Surface:
        """
        Get the current animation frame with fade effects applied.

        Returns:
            pygame.Surface: The current frame surface with fade alpha
        """
        if not self.frames:
            # Return a blank surface if no frames
            blank = pygame.Surface((1, 1), pygame.SRCALPHA)
            blank.fill((0, 0, 0, 0))
            return blank

        frame = self.frames[self.current_frame_index]

        # Apply fade effect if needed
        if self.fade_mode or self.fade_alpha != 255:
            return self._apply_fade_effect(frame)

        return frame

    def start_fade_in(self, duration: Optional[float] = None):
        """
        Start a fade-in effect.

        Args:
            duration (float, optional): Override fade-in duration. If None, uses initialized value.
        """
        if duration is not None:
            self.fade_in_duration = duration

        if self.fade_in_duration > 0:
            self.fade_mode = "in"
            self.fade_alpha = 0
            self.fade_start_time = time.time()
            self.fade_progress = 0.0
            self.playing = True

    def start_fade_out(self, duration: Optional[float] = None):
        """
        Start a fade-out effect.

        Args:
            duration (float, optional): Override fade-out duration. If None, uses initialized value.
        """
        if duration is not None:
            self.fade_out_duration = duration

        if self.fade_out_duration > 0:
            self.fade_mode = "out"
            self.fade_alpha = 255
            self.fade_start_time = time.time()
            self.fade_progress = 0.0

    def set_fade_alpha(self, alpha: int):
        """
        Manually set the fade alpha value.

        Args:
            alpha (int): Alpha value from 0 (transparent) to 255 (opaque)
        """
        self.fade_alpha = max(0, min(255, alpha))
        self.fade_mode = None  # Disable automatic fade when manually setting

    def is_fade_complete(self) -> bool:
        """
        Check if the current fade effect is complete.

        Returns:
            bool: True if no fade effect is active or fade is complete
        """
        return self.fade_mode is None

    def reset(self):
        """Reset the animation to the first frame and reset fade effects."""
        self.current_frame_index = 0
        self.accumulated_time = 0.0
        self.last_update_time = time.time()
        self.playing = True

        # Reset fade effects based on initialization
        if self.fade_in_duration > 0:
            self.fade_mode = "in"
            self.fade_alpha = 0
        else:
            self.fade_mode = None
            self.fade_alpha = 255

        self.fade_start_time = time.time() if self.fade_mode else None
        self.fade_progress = 0.0